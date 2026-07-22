# Bounded Concurrency Model

Use this model for all full and high-coverage runs. The pipeline follows Map-Barrier-Reduce: fan independent work out, wait for every task in the stage, reduce deterministically in input/source order, then start the dependent stage.

## Stages

1. **Citation discovery**: run Google Scholar, Semantic Scholar, OpenAlex, and OpenCitations concurrently with `--find-workers 4`. Keep Google Scholar pagination serial inside its single browser worker.
2. **Metadata expansion**: after OpenCitations returns DOI links, fetch Crossref metadata with `--metadata-workers 12` and pace request starts with `--metadata-rps 5`. Preserve the original DOI order after the barrier.
3. **Discovery reduction**: wait for all source workers, then merge and deduplicate. Never write a partial workbook while another source is still running.
   After the barrier, persist one independent snapshot per successful source. A 429/5xx/timeout may use a recent same-target snapshot labeled `cached_fallback`; do not retry a temporarily unavailable source in `skip` mode.
4. **Author metrics**: probe Semantic Scholar once in the default skip mode. Fan out independent author profiles with `--author-workers 8` only if the probe succeeds; on 429/5xx/timeout open a circuit and keep the skipped entries retryable. Keep Google Scholar profile access serial.
5. **Honor/homepage evidence**: use `--wiki-workers 4` for Wikipedia, Wikidata, direct homepages, and fallback homepage searches. Complete identity checks after all evidence tasks finish.
6. **PDF download**: use `--download-workers 8`. Each worker writes a distinct file; write the manifest after the barrier.
7. **PDF context analysis**: use `--analyze-workers 4`. Analyze separate PDFs concurrently, then reduce contexts in original paper order before writing Excel/HTML.
8. **Formal outputs**: write Excel, JSON, dashboard, and PDF serially. Never allow concurrent writers to the same artifact.

## Safety Rules

- Bound every pool; do not create one task per author without a semaphore/pool limit.
- Give each HTTP worker a thread-local `requests.Session`; do not share mutable sessions across threads.
- In the default `skip` policy, record and isolate 429/5xx/timeout immediately. Use provider-specific backoff only when the caller explicitly selects `retry`. Treat quota exhaustion as a source failure rather than retrying for hours.
- Isolate task failures. Preserve successful source results and record failed tasks in diagnostics.
- Preserve deterministic ordering after each barrier so repeated runs produce stable workbooks.
- Record stage worker counts, provider elapsed time, and stage elapsed time in `run_notes`.
- Lower workers when a provider starts returning 429 responses. Suggested conservative values: discovery 2, metadata 4, authors 4, evidence 2, downloads 4, analysis 2.

## Tuning

Measure changes with the quality-preserving speedup metric:

```powershell
python scripts/benchmark_concurrency.py `
  --paper "<title-or-doi>" `
  --output .\benchmark `
  --platforms opencitations
```

The benchmark disables source caches and reports `QPS = serial wall time / concurrent wall time` only when both runs are nonempty, their successful-source sets match, and deduplicated-paper Jaccard similarity plus author-metadata coverage are both at least 0.99. Otherwise QPS is zero.

For author-discovery coverage, use `scripts/benchmark_author_coverage.py` with an identity-disambiguated reference set. It reports Verified High-value Author Recall (VHAR); a name-only hit is insufficient.

Fast local/network profile:

```powershell
python scripts/paper_citation_researcher.py run `
  --paper "<title-or-doi>" --output .\out `
  --find-workers 4 --metadata-workers 16 `
  --author-workers 10 --wiki-workers 6 `
  --download-workers 12 --analyze-workers 6
```

Rate-limit-friendly profile:

```powershell
python scripts/paper_citation_researcher.py run `
  --paper "<title-or-doi>" --output .\out `
  --find-workers 2 --metadata-workers 4 `
  --author-workers 4 --wiki-workers 2 `
  --download-workers 4 --analyze-workers 2
```
