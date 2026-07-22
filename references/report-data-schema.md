# Report Data Contract

Use UTF-8 JSON with this top-level shape:

```json
{
  "target": {
    "title": "...", "authors": "...", "venue": "...", "year": 2022,
    "abstract": "...",
    "doi": "...", "citation_count": 15, "retrieved_at": "2026-07-15",
    "sources": [{"name": "OpenAlex", "url": "...", "coverage": "15 citing works"}]
  },
  "coverage": {
    "reported_citation_count_max": 72,
    "discovered_unique_citing_papers": 68,
    "source_success_count": 3,
    "source_counts": {"google-scholar": 68, "semantic-scholar": 55, "openalex": 60},
    "citing_papers_with_authors": 67,
    "unique_citing_authors": 241,
    "authors_profiled": 241,
    "high_value_candidates_reviewed": 28,
    "retained_scholars": 15,
    "retained_company_authors": 12,
    "retained_with_homepage": 21,
    "retained_with_verified_context": 13,
    "fulltext_attempted": 24,
    "fulltext_acquired": 16,
    "positive_contexts": 8,
    "search_passes": 2,
    "new_verified_people_last_pass": 0,
    "unresolved_candidates": 3
  },
  "scholars": [{
    "name": "...", "honor": "IEEE Fellow", "affiliation": "...",
    "h_index": 67, "personal_citation_count": 21576,
    "homepage": "https://...", "confidence": "high",
    "confidence_reason": "...", "honor_evidence": ["https://..."],
    "claim_verdicts": {"authorship": "supported", "target_citation": "supported",
      "honor_or_company": "supported", "homepage_identity": "supported",
      "context_assessment": "supported"},
    "citing_papers": [{"title": "...", "year": 2024, "venue": "...",
      "citation_count": 13, "target_citation_frequency": 1,
      "url": "https://...", "context": "...", "context_original": "...",
      "citation_role": "method", "assessment_type": "positive_assessment",
      "assessment_zh": "该引文在方法讨论中...", "positive_assessment": true,
      "context_status": "verified"}]
  }],
  "companies": [{
    "company": "...", "name": "...", "raw_affiliation": "...",
    "homepage": "", "confidence": "medium", "confidence_reason": "...",
    "affiliation_evidence": ["https://..."],
    "citing_papers": [{"title": "...", "year": 2024, "venue": "...",
      "url": "https://...", "context": "...", "context_status": "not-accessible"}]
  }],
  "diagnostics": {
    "zero_categories": ["Turing Award"],
    "excluded_candidates": [{"name": "...", "reason": "..."}],
    "limitations": ["..."], "notes": ["..."]
  }
}
```

Allowed confidence values: `high`, `medium`. Low-confidence candidates belong in `diagnostics.excluded_candidates`.

Allowed context states: `verified`, `reference-list-only`, `not-accessible`.

Allowed citation roles: `method`, `background`, `baseline`, `dataset`. A `verified` context must include `context_original`, one allowed `citation_role`, and a conservative Chinese `assessment_zh`. Keep the original wording visible; never label a neutral context as positive merely because the paper cites the target.

For every retained record, require a name, honor/company, confidence reason, at least one evidence URL, and at least one named citing paper. `homepage` may be empty only when no authoritative personal page was found and the confidence reason says so.

For high-coverage reports, include `coverage` and run `scripts/audit_report_quality.py --strict`. Read `references/quality-and-coverage-standard.md` for metric definitions and the saturation rule.
