import json
import sys
from pathlib import Path
from urllib.parse import urlparse

ALLOWED_CONFIDENCE = {"high", "medium"}
ALLOWED_CONTEXT = {"verified", "reference-list-only", "not-accessible"}
ALLOWED_VERDICTS = {"supported", "partially-supported", "uncertain", "unsupported"}
REQUIRED_CLAIMS = {"authorship", "target_citation", "honor_or_company", "homepage_identity", "context_assessment"}
BAD_TEXT = ("见pdf", "自动解析", "未自动拆分", "未能唯一对应", "TODO")

def is_url(value):
    try:
        return urlparse(value).scheme in {"http", "https"} and bool(urlparse(value).netloc)
    except Exception:
        return False

def main(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    errors = []
    target = data.get("target", {})
    high_coverage = bool(data.get("coverage"))
    for key in ("title", "retrieved_at", "sources"):
        if not target.get(key): errors.append(f"target.{key} is required")
    for group, label_key in (("scholars", "honor"), ("companies", "company")):
        for i, row in enumerate(data.get(group, []), 1):
            prefix = f"{group}[{i}]"
            for key in ("name", label_key, "confidence", "confidence_reason", "citing_papers"):
                if not row.get(key): errors.append(f"{prefix}.{key} is required")
            if row.get("confidence") not in ALLOWED_CONFIDENCE:
                errors.append(f"{prefix}.confidence must be high or medium")
            evidence_key = "honor_evidence" if group == "scholars" else "affiliation_evidence"
            if not row.get(evidence_key) or not all(is_url(x) for x in row[evidence_key]):
                errors.append(f"{prefix}.{evidence_key} requires valid URLs")
            if row.get("homepage") and not is_url(row["homepage"]):
                errors.append(f"{prefix}.homepage is not a valid URL")
            if not row.get("homepage") and "主页" not in row.get("confidence_reason", ""):
                errors.append(f"{prefix} has no homepage; explain this in confidence_reason")
            verdicts = row.get("claim_verdicts") or {}
            if high_coverage and set(verdicts) != REQUIRED_CLAIMS:
                errors.append(f"{prefix}.claim_verdicts must contain all five verification claims")
            for claim, verdict in verdicts.items():
                if claim not in REQUIRED_CLAIMS or verdict not in ALLOWED_VERDICTS:
                    errors.append(f"{prefix}.claim_verdicts.{claim} is invalid")
            if verdicts and (
                verdicts.get("authorship") != "supported"
                or verdicts.get("target_citation") != "supported"
                or verdicts.get("honor_or_company") != "supported"
            ):
                errors.append(f"{prefix} cannot enter the main table without supported identity, citation, and honor/company claims")
            for j, paper in enumerate(row.get("citing_papers", []), 1):
                if not paper.get("title"): errors.append(f"{prefix}.citing_papers[{j}].title is required")
                if paper.get("context_status") not in ALLOWED_CONTEXT:
                    errors.append(f"{prefix}.citing_papers[{j}].context_status is invalid")
    blob = json.dumps(data, ensure_ascii=False)
    for phrase in BAD_TEXT:
        if phrase.lower() in blob.lower(): errors.append(f"forbidden placeholder text: {phrase}")
    if errors:
        print("\n".join(f"ERROR: {x}" for x in errors)); return 1
    print(f"OK: {len(data.get('scholars', []))} scholars, {len(data.get('companies', []))} company authors")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
