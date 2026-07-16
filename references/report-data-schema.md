# Report Data Contract

Use UTF-8 JSON with this top-level shape:

```json
{
  "target": {
    "title": "...", "authors": "...", "venue": "...", "year": 2022,
    "doi": "...", "citation_count": 15, "retrieved_at": "2026-07-15",
    "sources": [{"name": "OpenAlex", "url": "...", "coverage": "15 citing works"}]
  },
  "scholars": [{
    "name": "...", "honor": "IEEE Fellow", "affiliation": "...",
    "homepage": "https://...", "confidence": "high",
    "confidence_reason": "...", "honor_evidence": ["https://..."],
    "citing_papers": [{"title": "...", "year": 2024, "venue": "...",
      "url": "https://...", "context": "...", "context_status": "not-accessible"}]
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

For every retained record, require a name, honor/company, confidence reason, at least one evidence URL, and at least one named citing paper. `homepage` may be empty only when no authoritative personal page was found and the confidence reason says so.
