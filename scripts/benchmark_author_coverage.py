import argparse
import json
import re
from pathlib import Path

import pandas as pd


def normalize(value):
    return " ".join(re.findall(r"[a-z0-9]+", str(value or "").lower()))


def token_overlap(left, right):
    a = set(normalize(left).split())
    b = set(normalize(right).split())
    return len(a & b) / len(a) if a else 0.0


def main():
    parser = argparse.ArgumentParser(description="Measure verified high-value author recall against a curated reference set")
    parser.add_argument("--workbook", required=True)
    parser.add_argument("--gold", required=True)
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    authors = pd.read_excel(args.workbook, sheet_name="authors").fillna("").to_dict("records")
    gold = json.loads(Path(args.gold).read_text(encoding="utf-8"))
    results = []
    for identity in gold.get("identities", []):
        same_name = [row for row in authors if normalize(row.get("name")) == normalize(identity.get("name"))]
        ranked = sorted(
            same_name,
            key=lambda row: token_overlap(
                identity.get("affiliation"),
                " | ".join(
                    str(row.get(field) or "")
                    for field in (
                        "source_affiliations",
                        "profile_affiliations",
                        "semantic_scholar_affiliations",
                        "google_scholar_affiliation",
                    )
                ),
            ),
            reverse=True,
        )
        best = ranked[0] if ranked else {}
        affiliation_score = token_overlap(
            identity.get("affiliation"),
            " | ".join(
                str(best.get(field) or "")
                for field in (
                    "source_affiliations",
                    "profile_affiliations",
                    "semantic_scholar_affiliations",
                    "google_scholar_affiliation",
                )
            ),
        ) if best else 0.0
        identity_matched = bool(best) and (len(same_name) == 1 or affiliation_score >= 0.5)
        profile_evidence = any(
            best.get(field)
            for field in (
                "personal_homepage_url",
                "wikipedia_url",
                "google_scholar_profile_url",
                "semantic_scholar_profile_url",
                "company_affiliation_evidence",
            )
        )
        verified = bool(
            identity_matched
            and best.get("citing_titles")
            and str(best.get("author_quality_tier") or "unverified") != "unverified"
            and profile_evidence
        )
        results.append(
            {
                **identity,
                "identity_matched": identity_matched,
                "affiliation_score": round(affiliation_score, 3),
                "verified_evidence_complete": verified,
                "matched_author_key": best.get("author_key", ""),
                "matched_quality_tier": best.get("author_quality_tier", ""),
            }
        )

    total = len(results)
    identity_hits = sum(item["identity_matched"] for item in results)
    verified_hits = sum(item["verified_evidence_complete"] for item in results)
    report = {
        "metric": "Verified High-value Author Recall (VHAR)",
        "formula": "reference identities with citing paper + verified quality tier + profile/company evidence / all reference identities",
        "reference_warning": gold.get("warning", ""),
        "reference_identities": total,
        "identity_matches": identity_hits,
        "identity_recall": round(identity_hits / total, 4) if total else 0.0,
        "verified_evidence_complete_matches": verified_hits,
        "vhar": round(verified_hits / total, 4) if total else 0.0,
        "details": results,
    }
    output = Path(args.output) if args.output else Path(args.workbook).with_name("author_coverage_benchmark.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "details"}, ensure_ascii=False, indent=2))
    print(f"Saved benchmark: {output}")


if __name__ == "__main__":
    main()
