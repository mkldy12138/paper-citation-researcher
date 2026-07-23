import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


SCRIPTS = Path(__file__).resolve().parent


with tempfile.TemporaryDirectory() as temp_dir:
    root = Path(temp_dir)
    workbook = root / "citation_report.xlsx"
    report_json = root / "report.json"
    evidence_pdf = root / "inspected-citing-paper.pdf"
    evidence_pdf.write_bytes(b"%PDF-1.4\n% test fixture\n")
    verified_contexts = root / "verified_citation_contexts.json"
    verified_contexts.write_text(
        json.dumps(
            {
                "target_title": "Target Paper",
                "contexts": [
                    {
                        "citing_title": "A Verified Citing Paper",
                        "context": "The inspected PDF explicitly adopts the Target Paper method.",
                        "citation_role": "method",
                        "assessment_type": "positive_assessment",
                        "is_positive": True,
                        "confidence": 0.99,
                        "page": 3,
                        "pdf_path": str(evidence_pdf),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    with pd.ExcelWriter(workbook, engine="openpyxl") as writer:
        pd.DataFrame(
            [
                {"record_type": "metadata", "field": "title", "value": "Target Paper"},
                {"record_type": "metadata", "field": "year", "value": 2024},
                {"record_type": "author", "author_name": "Target Author"},
            ]
        ).to_excel(writer, sheet_name="target", index=False)
        pd.DataFrame(
            [
                {
                    "citing_title": "A Verified Citing Paper",
                    "publication_year": 2026,
                    "venue": "Test Venue",
                    "doi": "10.1000/citing",
                    "url": "https://doi.org/10.1000/citing",
                    "citation_count": 12,
                    "analysis_status": "cited_in_body",
                    "download_status": "downloaded",
                    "citing_authors": "Jane Expert",
                }
            ]
        ).to_excel(writer, sheet_name="papers", index=False)
        pd.DataFrame(
            [{"author_key": "s2:jane", "citing_title": "A Verified Citing Paper"}]
        ).to_excel(writer, sheet_name="paper_authors", index=False)
        pd.DataFrame(
            [
                {
                    "author_key": "s2:jane",
                    "name": "Jane Expert",
                    "author_quality_tier": "ieee_fellow",
                    "professional_memberships": "IEEE Fellow",
                    "profile_affiliations": "Example University",
                    "source_affiliations": "NVIDIA Research",
                    "source_company_affiliations": "NVIDIA",
                    "company_affiliation_evidence": "Structured citing-paper institution",
                    "personal_homepage_url": "https://example.edu/jane",
                    "author_quality_reason": "Official profile verifies IEEE Fellow",
                    "semantic_scholar_h_index": 88,
                    "selected_citation_count": 30000,
                }
            ]
        ).to_excel(writer, sheet_name="authors", index=False)
        pd.DataFrame(
            [
                {
                    "citing_title": "A Verified Citing Paper",
                    "context": "We build on the Target Paper method and improve its efficiency.",
                    "citation_role": "method",
                    "assessment_type": "positive_assessment",
                    "is_positive": True,
                    "confidence": 0.98,
                }
            ]
        ).to_excel(writer, sheet_name="citation_locations", index=False)
        pd.DataFrame(
            [
                {"key": "find.platform_record_counts_json", "value": json.dumps({"openalex": 1, "semantic-scholar": 1})},
                {"key": "find.google_scholar.reported_cited_by_count", "value": 1},
                {"key": "authors.pass_number", "value": 1},
                {"key": "authors.pass_number", "value": 2},
                {"key": "authors.new_verified_people_this_pass", "value": 0},
            ]
        ).to_excel(writer, sheet_name="run_notes", index=False)

    subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "build_report_data.py"),
            "--workbook",
            str(workbook),
            "--output",
            str(report_json),
            "--verified-contexts",
            str(verified_contexts),
        ],
        check=True,
    )
    subprocess.run([sys.executable, str(SCRIPTS / "validate_report_data.py"), str(report_json)], check=True)
    report = json.loads(report_json.read_text(encoding="utf-8"))
    assert len(report["scholars"]) == 1
    assert len(report["companies"]) == 1
    evidence = report["scholars"][0]["citing_papers"][0]
    assert evidence["title"] == "A Verified Citing Paper"
    assert evidence["context_original"].startswith("The inspected PDF")
    assert evidence["page"] == "3"
    assert evidence["evidence_pdf"] == str(evidence_pdf)
    assert evidence["citation_role"] == "method"
    assert evidence["assessment_zh"]
    assert evidence["positive_assessment"] is True

print("OK report-data evidence pipeline")
