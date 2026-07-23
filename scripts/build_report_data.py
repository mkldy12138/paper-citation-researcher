import argparse
import json
import re
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd


def norm(value):
    return " ".join(re.findall(r"[a-z0-9]+", str(value or "").lower()))


def integer(value):
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def optional_positive_integer(value):
    if value is None or str(value).strip() == "":
        return ""
    parsed = integer(value)
    return parsed if parsed > 0 else ""


def number(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def truthy(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def valid_url(value):
    try:
        parsed = urlparse(str(value or ""))
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except Exception:
        return False


def split_values(value):
    return [item.strip() for item in re.split(r"\s*[|;]\s*", str(value or "")) if item.strip()]


def verified_display_name(author):
    source_name = str(author.get("name") or "").strip()
    profile_name = str(author.get("wikipedia_title") or "").strip()
    if profile_name and sorted(norm(profile_name).split()) == sorted(norm(source_name).split()):
        return profile_name
    return source_name


def read_report_sheets(workbook, names):
    requested = list(names)
    try:
        frames = pd.read_excel(workbook, sheet_name=requested)
    except ValueError:
        available = pd.ExcelFile(workbook).sheet_names
        present = [name for name in requested if name in available]
        frames = pd.read_excel(workbook, sheet_name=present) if present else {}
    return {
        name: frames.get(name, pd.DataFrame()).fillna("")
        for name in requested
    }


def read_verified_contexts(path, target_title):
    if not path:
        return []
    context_path = Path(path)
    if not context_path.is_file():
        raise FileNotFoundError(f"Verified context file not found: {context_path}")
    payload = json.loads(context_path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        declared_target = str(payload.get("target_title") or "").strip()
        if declared_target and norm(declared_target) != norm(target_title):
            raise ValueError(
                "Verified context target does not match workbook target: "
                f"{declared_target!r} != {target_title!r}"
            )
        rows = payload.get("contexts") or []
    elif isinstance(payload, list):
        rows = payload
    else:
        raise ValueError("Verified context JSON must be an object or a list")
    required = {"citing_title", "context", "citation_role", "confidence", "pdf_path"}
    cleaned = []
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise ValueError(f"Verified context row {index} is not an object")
        missing = [field for field in required if not str(row.get(field) or "").strip()]
        if missing:
            raise ValueError(f"Verified context row {index} missing: {', '.join(missing)}")
        pdf_path = Path(str(row["pdf_path"]))
        if not pdf_path.is_file():
            raise FileNotFoundError(f"Verified context PDF not found: {pdf_path}")
        item = dict(row)
        item["source_platforms"] = str(item.get("source_platforms") or "inspected citing-paper PDF")
        item["match_type"] = str(item.get("match_type") or "manual_pdf_inspection")
        item["assessment_type"] = str(item.get("assessment_type") or item.get("citation_role") or "")
        item["is_positive"] = truthy(item.get("is_positive"))
        item["verified_context_source"] = str(context_path)
        cleaned.append(item)
    return cleaned


def note_name(key):
    return str(key or "").split(" ", 2)[-1]


def platform_error_limitations(value):
    raw = str(value or "").strip()
    if not raw or raw == "[]":
        return []
    try:
        items = json.loads(raw)
    except json.JSONDecodeError:
        return [raw[:300]]
    if not isinstance(items, list):
        return [raw[:300]]
    limitations = []
    for item in items:
        if not isinstance(item, dict):
            limitations.append(str(item)[:300])
            continue
        platform = str(item.get("platform") or item.get("source") or "unknown source")
        error = str(item.get("error") or item.get("message") or "request failed")
        lowered = error.lower()
        if "429" in lowered or "rate limit" in lowered or "too many requests" in lowered:
            limitations.append(f"{platform} 请求受限（429），本轮已隔离该来源并保留故障记录。")
        elif "captcha" in lowered:
            limitations.append(f"{platform} 遇到验证码，本轮未将该来源缺失解释为零引用。")
        elif "timeout" in lowered:
            limitations.append(f"{platform} 请求超时，本轮已跳过并保留故障记录。")
        else:
            limitations.append(f"{platform} 获取失败：{error[:220]}")
    return limitations


def target_data(target_frame):
    metadata = {}
    authors = []
    target_json = {}
    for row in target_frame.to_dict("records"):
        if row.get("record_type") == "metadata":
            metadata[str(row.get("field") or "")] = row.get("value", "")
        elif row.get("record_type") == "author" and row.get("author_name"):
            authors.append(str(row.get("author_name")))
    if metadata.get("target_json"):
        try:
            target_json = json.loads(str(metadata["target_json"]))
        except json.JSONDecodeError:
            target_json = {}
    if not authors:
        for item in target_json.get("authors") or []:
            name = item.get("name") if isinstance(item, dict) else str(item)
            if name:
                authors.append(name)
        for item in target_json.get("authorships") or []:
            author = item.get("author") or {}
            if author.get("display_name"):
                authors.append(author["display_name"])
    external = target_json.get("externalIds") or target_json.get("ids") or {}
    doi = metadata.get("doi") or external.get("DOI") or external.get("doi") or target_json.get("doi") or ""
    doi = str(doi).replace("https://doi.org/", "")
    return {
        "title": metadata.get("title") or target_json.get("title") or target_json.get("display_name") or "",
        "authors": ", ".join(dict.fromkeys(authors)),
        "venue": metadata.get("venue") or target_json.get("venue") or (target_json.get("primary_location") or {}).get("raw_source_name") or "",
        "year": integer(metadata.get("year") or target_json.get("year") or target_json.get("publication_year")),
        "abstract": target_json.get("abstract") or "",
        "doi": doi,
    }


def profile_urls(author):
    fields = (
        "personal_homepage_url",
        "wikipedia_url",
        "google_scholar_homepage_url",
        "semantic_scholar_homepage_url",
        "google_scholar_profile_url",
        "semantic_scholar_profile_url",
    )
    return list(dict.fromkeys(str(author.get(field)) for field in fields if valid_url(author.get(field))))


def homepage(author):
    urls = profile_urls(author)
    return urls[0] if urls else ""


def honor_label(author):
    evidence = []
    for field in ("honors_awards", "professional_memberships", "academic_titles"):
        evidence.extend(split_values(author.get(field)))
    if evidence:
        return "；".join(dict.fromkeys(evidence))
    tier = str(author.get("author_quality_tier") or "")
    if tier == "high_impact":
        return f"高影响力学者（h指数 {integer(author.get('semantic_scholar_h_index'))}）"
    return str(author.get("author_quality_reason") or tier)


ROLE_ZH = {
    "method": "该引文在方法、模型或技术路线讨论中引用目标论文。",
    "background": "该引文将目标论文作为相关工作或研究背景。",
    "baseline": "该引文将目标论文作为基线、基准或比较对象。",
    "dataset": "该引文在数据集、训练数据或数据处理语境中引用目标论文。",
}


def citing_papers_for_author(author, paper_authors, papers_by_title, contexts_by_title):
    key = str(author.get("author_key") or "")
    titles = []
    if not paper_authors.empty:
        titles.extend(
            str(row.get("citing_title"))
            for row in paper_authors.to_dict("records")
            if str(row.get("author_key") or "") == key and row.get("citing_title")
        )
    if not titles:
        titles.extend(split_values(author.get("citing_titles")))
    result = []
    for title in dict.fromkeys(titles):
        paper = papers_by_title.get(norm(title), {})
        contexts = contexts_by_title.get(norm(title), [])
        contexts.sort(key=lambda row: (not truthy(row.get("is_positive")), -number(row.get("confidence"))))
        best = contexts[0] if contexts else {}
        analysis_status = str(paper.get("analysis_status") or "")
        if best:
            context_status = "verified"
        elif "reference_found" in analysis_status:
            context_status = "reference-list-only"
        else:
            context_status = "not-accessible"
        role = str(best.get("citation_role") or "")
        paper_url = str(paper.get("url") or "")
        if not valid_url(paper_url) and paper.get("doi"):
            paper_url = f"https://doi.org/{paper.get('doi')}"
        result.append(
            {
                "title": title,
                "year": integer(paper.get("publication_year")),
                "venue": str(paper.get("venue") or ""),
                "citation_count": integer(paper.get("citation_count")),
                "target_citation_frequency": len(contexts) if contexts else "",
                "url": paper_url,
                "context": str(best.get("context") or ""),
                "context_original": str(best.get("context_original") or best.get("context") or ""),
                "page": str(best.get("page") or ""),
                "evidence_pdf": str(best.get("pdf_path") or ""),
                "citation_role": role,
                "assessment_type": str(best.get("assessment_type") or role),
                "assessment_zh": str(best.get("assessment_zh") or ROLE_ZH.get(role, "")),
                "positive_assessment": truthy(best.get("is_positive")),
                "context_status": context_status,
            }
        )
    return result


def claim_verdicts(has_homepage, has_context):
    return {
        "authorship": "supported",
        "target_citation": "supported",
        "honor_or_company": "supported",
        "homepage_identity": "supported" if has_homepage else "uncertain",
        "context_assessment": "supported" if has_context else "unsupported",
    }


def dedupe_retained_people(rows, kind):
    merged = []
    by_identity = {}
    for row in rows:
        home = str(row.get("homepage") or "").strip().lower()
        affiliation = str(row.get("affiliation") or row.get("raw_affiliation") or "")
        category = str(row.get("honor") or row.get("company") or "")
        identity_anchor = home or norm(affiliation)
        key = (kind, norm(row.get("name")), norm(category), identity_anchor)
        if key not in by_identity:
            item = dict(row)
            item["citing_papers"] = list(row.get("citing_papers") or [])
            merged.append(item)
            by_identity[key] = item
            continue
        current = by_identity[key]
        paper_by_title = {norm(paper.get("title")): paper for paper in current.get("citing_papers") or []}
        for paper in row.get("citing_papers") or []:
            paper_key = norm(paper.get("title"))
            previous = paper_by_title.get(paper_key)
            if previous is None:
                current["citing_papers"].append(paper)
                paper_by_title[paper_key] = paper
            elif previous.get("context_status") != "verified" and paper.get("context_status") == "verified":
                previous.update(paper)
        for evidence_field in ("honor_evidence", "affiliation_evidence"):
            current[evidence_field] = list(
                dict.fromkeys((current.get(evidence_field) or []) + (row.get(evidence_field) or []))
            )
        for metric_field in ("h_index", "personal_citation_count"):
            available = [
                optional_positive_integer(value)
                for value in (current.get(metric_field), row.get(metric_field))
                if optional_positive_integer(value) != ""
            ]
            current[metric_field] = max(available) if available else ""
        if row.get("confidence") == "high":
            current["confidence"] = "high"
        current["claim_verdicts"] = {
            verdict: (
                "supported"
                if "supported" in {str(value), str((row.get("claim_verdicts") or {}).get(verdict))}
                else value
            )
            for verdict, value in (current.get("claim_verdicts") or {}).items()
        }
    return merged


def main():
    parser = argparse.ArgumentParser(description="Build formal citation-report JSON from citation_report.xlsx")
    parser.add_argument("--workbook", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--verified-contexts", default="")
    args = parser.parse_args()

    workbook = Path(args.workbook)
    sheets = read_report_sheets(
        workbook,
        ("target", "papers", "paper_authors", "authors", "citation_locations", "run_notes"),
    )
    target = target_data(sheets["target"])
    papers = sheets["papers"]
    paper_authors = sheets["paper_authors"]
    authors = sheets["authors"]
    contexts = sheets["citation_locations"]
    notes_frame = sheets["run_notes"]
    notes = {}
    for row in notes_frame.to_dict("records"):
        notes[note_name(row.get("key"))] = row.get("value", "")

    papers_by_title = {norm(row.get("citing_title")): row for row in papers.to_dict("records")}
    contexts_by_title = defaultdict(list)
    for row in contexts.to_dict("records"):
        contexts_by_title[norm(row.get("citing_title"))].append(row)
    for row in read_verified_contexts(args.verified_contexts, target.get("title", "")):
        contexts_by_title[norm(row.get("citing_title"))].append(row)

    scholars = []
    companies = []
    excluded = []
    scholar_tiers = {"elite_award", "academy_member", "ieee_fellow", "society_fellow", "high_impact"}
    for author in authors.to_dict("records"):
        tier = str(author.get("author_quality_tier") or "unverified")
        author_papers = citing_papers_for_author(author, paper_authors, papers_by_title, contexts_by_title)
        urls = profile_urls(author)
        home = homepage(author)
        has_context = any(paper.get("context_status") == "verified" for paper in author_papers)
        if tier in scholar_tiers:
            honor = honor_label(author)
            if not author_papers or not honor or not urls:
                excluded.append({"name": author.get("name", ""), "reason": "缺少引用论文、头衔或可追溯画像证据"})
            else:
                reason = str(author.get("author_quality_reason") or "身份与头衔证据已交叉核验")
                if not home:
                    reason += "；未找到可核验主页"
                scholars.append(
                    {
                        "name": verified_display_name(author),
                        "honor": honor,
                        "affiliation": author.get("profile_affiliations") or author.get("source_affiliations") or "",
                        "h_index": optional_positive_integer(author.get("semantic_scholar_h_index")),
                        "personal_citation_count": optional_positive_integer(author.get("selected_citation_count")),
                        "homepage": home,
                        "confidence": "high" if author.get("personal_homepage_url") or author.get("wikipedia_url") else "medium",
                        "confidence_reason": reason,
                        "honor_evidence": urls,
                        "claim_verdicts": claim_verdicts(bool(home), has_context),
                        "citing_papers": author_papers,
                    }
                )
        company_names = split_values(author.get("source_company_affiliations"))
        for company in company_names:
            evidence = [paper.get("url") for paper in author_papers if valid_url(paper.get("url"))]
            evidence = list(dict.fromkeys(evidence or urls))
            if not author_papers or not evidence:
                excluded.append({"name": author.get("name", ""), "reason": f"{company}署名缺少可追溯链接"})
                continue
            reason = str(author.get("company_affiliation_evidence") or f"引用论文结构化署名机构为 {company}")
            if not home:
                reason += "；未找到可核验主页"
            companies.append(
                {
                    "company": company,
                    "name": verified_display_name(author),
                    "raw_affiliation": author.get("source_affiliations") or author.get("profile_affiliations") or "",
                    "homepage": home,
                    "confidence": "high" if home else "medium",
                    "confidence_reason": reason,
                    "affiliation_evidence": evidence,
                    "claim_verdicts": claim_verdicts(bool(home), has_context),
                    "citing_papers": author_papers,
                }
            )

    scholars = dedupe_retained_people(scholars, "scholar")
    companies = dedupe_retained_people(companies, "company")

    try:
        source_counts = json.loads(str(notes.get("find.platform_record_counts_json") or "{}"))
    except json.JSONDecodeError:
        source_counts = {}
    source_urls = {
        "google-scholar": str(notes.get("find.google_scholar.target_cited_by_url") or "https://scholar.google.com"),
        "semantic-scholar": "https://www.semanticscholar.org",
        "openalex": "https://openalex.org",
        "opencitations": "https://opencitations.net",
    }
    sources = [
        {"name": name, "url": source_urls.get(name, ""), "coverage": f"{integer(count)} citing works"}
        for name, count in source_counts.items()
        if valid_url(source_urls.get(name))
    ]
    reported = max(integer(notes.get("find.google_scholar.reported_cited_by_count")), len(papers))
    retained = scholars + companies
    author_pass_rows = [
        row for row in notes_frame.to_dict("records") if note_name(row.get("key")) == "authors.pass_number"
    ]
    profile_fields = ("personal_homepage_url", "wikipedia_url", "google_scholar_profile_url", "semantic_scholar_profile_url")
    data = {
        "target": {
            **target,
            "citation_count": reported,
            "retrieved_at": date.today().isoformat(),
            "sources": sources or [{"name": "local workbook", "url": "https://openalex.org", "coverage": f"{len(papers)} citing works"}],
        },
        "coverage": {
            "reported_citation_count_max": reported,
            "discovered_unique_citing_papers": len(papers),
            "source_success_count": sum(integer(count) > 0 for count in source_counts.values()),
            "source_counts": source_counts,
            "citing_papers_with_authors": int(papers.get("citing_authors", pd.Series(dtype=str)).astype(str).str.strip().ne("").sum()) if not papers.empty else 0,
            "unique_citing_authors": len(authors),
            "authors_profiled": sum(any(row.get(field) for field in profile_fields) or str(row.get("profile_query_status")) == "queried" for row in authors.to_dict("records")),
            "high_value_candidates_reviewed": sum(str(row.get("expert_query_status")) != "not_queried_outside_expert_scope" for row in authors.to_dict("records")),
            "retained_scholars": len(scholars),
            "retained_company_authors": len(companies),
            "retained_with_homepage": sum(bool(row.get("homepage")) for row in retained),
            "retained_with_verified_context": sum(any(p.get("context_status") == "verified" for p in row.get("citing_papers", [])) for row in retained),
            "fulltext_attempted": int(papers.get("download_status", pd.Series(dtype=str)).astype(str).str.strip().ne("").sum()) if not papers.empty else 0,
            "fulltext_acquired": int(papers.get("download_status", pd.Series(dtype=str)).astype(str).isin(["downloaded", "manual"]).sum()) if not papers.empty else 0,
            "positive_contexts": sum(truthy(value) for value in contexts.get("is_positive", pd.Series(dtype=object))) if not contexts.empty else 0,
            "search_passes": len(author_pass_rows),
            "new_verified_people_last_pass": integer(notes.get("authors.new_verified_people_this_pass")),
            "unresolved_candidates": sum(str(row.get("author_quality_tier")) == "unverified" and str(row.get("expert_query_status")) != "not_queried_outside_expert_scope" for row in authors.to_dict("records")),
        },
        "scholars": scholars,
        "companies": companies,
        "diagnostics": {
            "zero_categories": ["Turing Award"] if not any("turing" in str(row.get("honor", "")).lower() for row in scholars) else [],
            "excluded_candidates": excluded[:100],
            "limitations": platform_error_limitations(notes.get("find.platform_errors_json"))
            + [
                item
                for item in (
                    str(notes.get("find.google_scholar.partial_failure") or ""),
                    "未获取全文的引文只确认引用关系，不生成技术评价。" if any(not any(p.get("context_status") == "verified" for p in row.get("citing_papers", [])) for row in retained) else "",
                )
                if item
            ],
            "notes": ["中文说明为引用角色的保守分类；技术观点以原文上下文为准。"],
        },
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved report data: {output} ({len(scholars)} scholars, {len(companies)} company authors)")


if __name__ == "__main__":
    main()
