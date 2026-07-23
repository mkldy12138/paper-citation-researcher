---
name: paper-citation-researcher
description: Investigate high-value citations to one or more academic papers and deliver an evidence-backed Chinese PDF report, with Excel and HTML retained as supporting audit artifacts. Focus on Turing Award and other elite-prize recipients, academy members, Royal Society Fellows, verified IEEE Fellows, positive technical assessments, and authors affiliated with major international technology companies. Use when Codex must merge Google Scholar/Semantic Scholar/OpenAlex evidence with user-provided citation PDFs or Markdown, resolve names conservatively, deliver one detailed worksheet per target paper, or produce a polished high-value citation impact PDF.
---

# Paper Citation Researcher

Use this skill only for focused high-value citation research. Do not make a broad ordinary-author impact ranking the primary deliverable.

## Required Default Workflow

1. Read every target paper from the supplied workbook or list and preserve target order.
2. Discover citing papers through Semantic Scholar, OpenAlex, and OpenCitations/Crossref by default. Keep Google Scholar disabled unless the user explicitly requests it. Record platform failures explicitly; require at least two successful sources, and never interpret an unavailable source as zero citations.
3. Inspect every user-provided citation PDF, Markdown, workbook, or exported report. Match it to a target by normalized title. Put unrelated files in an `unmatched citation files` table; never attach them to a similar target.
   - Remove report watermarks, repeated headers, page numbers, and extraction artifacts such as repeated `AMiner 亮点` before writing cells.
   - Parse and display the reported author, honor/title, h-index, citation count, institution, citing-paper title, and available citation context as separate fields. Never use `see PDF`, `见PDF`, or similar placeholders for information that exists in the source.
   - Keep the local PDF/Markdown path only in an evidence-source column.
4. Retain only high-value people in the main author result: Turing Award or comparable elite-prize recipients, national academy/engineering academy members, Royal Society Fellows, and identity-verified IEEE Fellows. Keep honor classes separate.
5. Resolve authors by stable author ID first. Treat exact names alone as insufficient for common names. Before profile lookup, reconcile DOI-bearing citing-paper author lists against Crossref metadata. A hard name correction is allowed only when the title matches, author count/order agree, exactly one position conflicts, at least three other positions align, the surname agrees, and the canonical record supplies affiliation evidence. Preserve the original name and source ID, but do not attach a conflicting Semantic Scholar author ID to the corrected person. Initials, accents, spacing, hyphens, and omitted middle names are canonical variants and retain their stable ID. For a hard correction, reverse-resolve the canonical name through DBLP and require exact-name plus affiliation disambiguation before accepting its official homepage/ORCID. Follow a same-site biography page when present. Never accept Semantic Scholar's highest-cited name-search result when no strict name-equivalent candidate exists. Cross-check field, affiliation, citing-paper authorship, and source-profile evidence. Prefer a false negative to a false positive.
6. Query OpenAlex authorship institutions and parse institutions from user-provided reports to find major international technology-company citations. Include Google/DeepMind, Microsoft, Meta, NVIDIA, Amazon, Apple, Adobe, Intel, IBM, ByteDance, Tencent, Alibaba, Huawei, Samsung, Waymo, OpenAI, and other clearly comparable global research companies. Require the author, company, and citing-paper title to share one evidence record.
7. Report the exact citing-paper title for every retained person or company. Include evidence URLs/local paths, author ID when available, affiliation, honor, and a confidence or identity note. Add a `homepage/profile details` field using an identity-verified personal, university, organization, Google Scholar, Semantic Scholar, OpenAlex, or authoritative biographical page; leave it blank when no verified URL exists.
8. For multiple targets, write one worksheet per target paper plus a short overview and an unmatched-files worksheet. Do not place all target details into one combined sheet.
9. Do not download and analyze every citing PDF by default. Download only retained high-value citing papers when body-context evidence is requested or needed to resolve ambiguity.
10. For every normal user-facing investigation, convert the verified retained records to `references/report-data-schema.md`, validate the JSON, and render a formal Chinese PDF. Excel and HTML are supporting audit artifacts, not substitutes for the PDF. A request is not complete while only `citation_report.xlsx`, `citation_dashboard.html`, or `report.json` exists.
11. For AMiner-scale or exhaustive requests, read `references/quality-and-coverage-standard.md`, expand every citing author, complete at least two enrichment passes, and run the strict quality audit before rendering.
12. For full runs, read `references/concurrency-model.md`. Use bounded Map-Barrier-Reduce concurrency: fan out independent sources/tasks, wait for the entire stage, merge deterministically, then start the dependent stage.
13. When the user expects AMiner/MotionGPT-scale author coverage, read `references/motiongpt-benchmark-lessons.md`. Preserve structured citing-author institutions, run honor/company-targeted deep searches, and deliver a strict high-value layer plus a separately labeled high-impact supplement.
14. In detailed-report mode, keep exactly one person in each evidence block. For every named citing paper, show the original body context first, then its role (`method`, `background`, `baseline`, or `dataset`) and a specific conservative Chinese technical explanation. A generic role sentence is only a draft and must be refined before final delivery.
   - When an independently downloaded citing PDF is inspected outside `analyze`, save its verified body context in `OUTPUT/verified_citation_contexts.json`. Include the exact target title, citing-paper title, original context, role, confidence, local PDF path, and page. This file may enrich context only; never use it to create authorship, citation, or honor claims. The `report` command loads it automatically and rejects target-title mismatches or missing PDFs.
15. Treat the first generated PDF as a review artifact. A final detailed PDF requires at least two enrichment passes, zero newly verified people in the last pass, per-person citing-paper evidence, and rendered-page inspection.
16. Deliver the final PDF file directly in the response using its absolute clickable path. Do not finish with commands, source files, Excel, HTML, or a description of how the user could generate it. Report the page count and visual-QA result alongside the link.

## High-Value Reporting Rules

- Prioritize citing papers whose full text contains an explicit, favorable technical assessment of the target method. Distinguish `positive assessment`, `method adoption/comparison`, and `bibliographic mention`; never rewrite a neutral mention as praise.
- Write one scholar per evaluation entry. Use this order: full verified titles, scholar name, exact citing-paper title and venue/year, the scholar's specific assessment, target-paper identifier, and evidence source.
- Preserve the citing paper's wording and technical meaning. Paraphrase conservatively in Chinese and retain a short verified context field; do not fabricate evaluation language when full text is unavailable.
- Apply name language by academy affiliation, not ethnicity: use Chinese names for members of the Chinese Academy of Sciences or Chinese Academy of Engineering; use the authoritative English name for members of foreign academies and overseas Fellows, even when a Chinese name exists.
- Prefer relevant Chinese and US national-academy members, then verified IEEE Fellows. Add major-company authors only when the author is intrinsically notable or the company affiliation is directly supported by the citing paper.
- Never claim Turing Award citations unless the citing author is a verified laureate and the citing-paper authorship is identity-resolved. Report zero explicitly when none are verified.
- Add `confidence`, `confidence reason`, `homepage/profile`, `honor evidence`, `company-affiliation evidence`, exact citing-paper title, and citation context to every retained row.
- For multi-paper delivery, create separate scholar and company worksheets for each target. Keep exactly one final workbook; preserve user source files, citation PDFs, and requested summary documents when cleaning intermediates.
- Match detailed benchmark reports on search depth and per-person evidence density, not by padding the list. H-index alone never qualifies a person for the core table.
- Decompose every retained row into five claims: citing-paper authorship, exact target citation, honor/company affiliation, homepage identity, and citation-context assessment. Store a verdict for each claim.
- Repeat roster reverse-matching and unresolved-candidate searches until a final pass produces no new verified people. Record pass yield, coverage, and unresolved candidates.

## Quick Start

Run the full workflow:

```powershell
python scripts/paper_citation_researcher.py run --paper "Attention Is All You Need" --output ".\citation-output" --max-papers 1000 --find-workers 3 --metadata-workers 12 --author-workers 8 --wiki-workers 4 --download-workers 8 --analyze-workers 4
```

The default `run` command also creates `report.json` and `pdf/high-value-citation-report.pdf`. Rebuild a formal report from an existing workbook with:

```powershell
python scripts/paper_citation_researcher.py report --output .\output --strict-report
```

Render the PDF to images with Poppler (`pdftoppm -png`) or an equivalent renderer and inspect every page for clipped tables, overlaps, broken Chinese glyphs, and unreadable URLs. Do not deliver an uninspected PDF.

Run phases separately:

```powershell
python scripts/paper_citation_researcher.py find --paper "<title-or-doi>" --output ".\out"
python scripts/paper_citation_researcher.py authors --output ".\out"
python scripts/paper_citation_researcher.py download --output ".\out" --download-workers 4
python scripts/paper_citation_researcher.py analyze --output ".\out"
python scripts/paper_citation_researcher.py dashboard --output ".\out"
python scripts/paper_citation_researcher.py report --output ".\out" --strict-report
```

The required user-facing output is the inspected Chinese PDF. The primary supporting tabular artifact is `citation_report.xlsx`. The script can read older output directories that still contain CSV files; after a successful workbook write, legacy table files are removed unless `--export-legacy-csv` is explicitly supplied.

## Initial Setup

When using this skill on a new machine or from a project-local copy, initialize the environment before running workflows:

```powershell
cd path\to\paper-citation-researcher
py -m pip install -r requirements.txt
```

Use `python` instead of `py` on systems where the Python launcher is unavailable. Run commands from the skill directory, or keep the `scripts/paper_citation_researcher.py` path relative to the skill copy.

Required runtime setup:

- Python 3.10+.
- A supported browser is required only when Google Scholar is explicitly enabled. Edge is the default (`--browser edge`).
- Network access to Semantic Scholar Graph API, OpenAlex, OpenCitations/Crossref, publisher pages, arXiv, ACL Anthology, Wikipedia, and Wikidata.
- Write access to the chosen output directory.

Optional configuration:

- `SEMANTIC_SCHOLAR_API_KEY`: set this environment variable to use authenticated Semantic Scholar requests. Leave it unset for anonymous requests.
- `OPENALEX_API_KEY`: set this when OpenAlex requires paid or prepaid API credits. Budget exhaustion must be recorded as a platform failure, not zero citations.
- `--s2-api-key` / `--s2-api-key-env`: use these only when overriding the default API-key source.
- `--scholar-locale`: defaults to `zh-CN` for paper search and `en` for author profile search.
- `--max-papers`: defaults to `1000`; confirm this value at the start of each new target-paper topic.
- `--platforms`: defaults to `semantic-scholar,openalex,opencitations`. Add `google-scholar` explicitly only when browser verification is acceptable.
- `--find-workers`: defaults to `3`; starts the three default citation sources concurrently. Opt-in Google Scholar remains one browser session with serial pagination.
- `--metadata-workers`: defaults to `12`; concurrently enriches OpenCitations DOI records through Crossref after citation-link discovery.
- `--metadata-rps`: defaults to `5`; rate-limits async Crossref request starts so concurrency does not reduce metadata coverage.
- `--async-http` / `--no-async-http`: defaults to enabled; reuse one `aiohttp` connection pool for Crossref metadata.
- `--source-failure-policy skip|retry`: defaults to `skip`; immediately isolate a discovery source on 429, temporary 5xx, timeout, captcha, or exhausted quota.
- `--source-cache` / `--no-source-cache`: defaults to enabled. On a temporary live-source failure, reuse only a recent successful snapshot for the same normalized target and label it `cached_fallback`; never represent cached evidence as a fresh response.
- `--source-cache-max-age-hours`: defaults to `168`. Older snapshots are ignored.
- `--scholar-target-url`: optional exact Google Scholar citation-detail URL or `/scholar?cites=...` URL. Prefer it when the user supplies one; the detail-page title is still identity-checked before collection.
- `--minimum-source-success`: defaults to `2`; fail high-coverage discovery when fewer than two platforms return records.
- `--require-google-scholar`: opt in to Google Scholar and fail `find`/`run` if it produces no citing rows, while still writing failure diagnostics to `citation_report.xlsx`.
- `--scholar-captcha-action wait|fail`: defaults to `fail` during discovery so other sources continue; explicitly choose `wait` when manual Google Scholar completion is required.
- `--scholar-captcha-timeout`: defaults to `600` seconds; maximum wait time for manual Google Scholar verification.
- `--author-workers`: defaults to `8`; controls parallel Semantic Scholar Author API profile queries.
- `--author-failure-policy skip|retry`: defaults to `skip`; probe Semantic Scholar once and open a circuit on 429/5xx/timeout before queuing hundreds of author requests. Skipped entries remain retryable on the next run.
- `--canonical-author-metadata` / `--no-canonical-author-metadata`: DOI author-name and affiliation reconciliation is enabled by default.
- `--canonical-author-workers`: defaults to `8`; concurrently retrieves independent Crossref DOI metadata records.
- `--canonical-author-rps`: defaults to `5`; bounds Crossref request starts during author canonicalization.
- `--wiki-workers`: defaults to `4`; controls parallel Wikipedia/Wikidata and homepage enrichment.
- `--download-workers`: defaults to `8`; downloads distinct citing PDFs concurrently.
- `--analyze-workers`: defaults to `4`; analyzes distinct local PDFs concurrently before ordered reduction.
- `--download-scope`: full `run` defaults to `high-value`; after author selection it downloads only citing papers represented in the retained notable set. Use `all` only when complete full-text analysis is explicitly required.
- `--formal-report` / `--no-formal-report`: defaults to enabled for full runs; generates validated JSON and a Chinese PDF after the workbook and dashboard.
- `--strict-report`: fails report generation when discovery, saturation, homepage, or body-context evidence thresholds are incomplete.
- `--verified-contexts`: supplies an inspected-PDF context JSON; defaults to `OUTPUT/verified_citation_contexts.json` when that file exists.
- `--author-top-n`: defaults to `100`; controls priority roster and biographical enrichment.
- `--max-author-profiles`: defaults to `1000`; covers the complete citing-author pool for detailed investigations.
- `--homepage-search-limit`: defaults to `250`; for expert-scope authors without a known profile homepage, searches for likely personal/school homepages and extracts profile evidence.
- `--author-quality-scope`: defaults to `high-impact`, so the selected output includes verified elite-award recipients, academy members/Royal Society Fellows, IEEE Fellows, directly evidenced major-company authors, and identity-verified metric-threshold scholars. Use `high-value` to omit metric-only scholars, `elite` for awards/academies only, or `all-notable` only for debugging.
- `--google-scholar-authors`: opt in to serial Google Scholar author-profile queries. They are skipped by default; cached profiles remain available.
- `--export-legacy-csv`: debugging option that also writes old CSV/XLSX tables. Do not use it for normal runs.

No OpenAI or LLM API key is required for find/authors/download/analyze/dashboard. Author enrichment uses deterministic page/API retrieval and caches results.

When downloads fail, open `citation_report.xlsx`, sheet `manual_download_todo`. Download those PDFs manually, then either:

- save each PDF to its `expected_pdf_path`, or
- fill `manual_pdf_path` with the actual local PDF path.

Then rerun `analyze`; it automatically includes manually supplied PDFs.

## Before Running

For each new target-paper topic, ask whether to use the default `--max-papers 1000` before starting. Within an ongoing workflow for the same target paper, use defaults without re-asking unless the required paper identifier or output directory is missing, or the user explicitly wants to customize parameters.

Required values:

- Target paper identifier: title or DOI.
- Output directory.

When the user asks what can be changed, explain only the relevant phase:

- `find`: `--platforms`, `--max-papers`, `--find-workers`, `--metadata-workers`, `--metadata-rps`, `--async-http`, `--source-failure-policy`, `--source-cache`, `--source-cache-max-age-hours`, `--scholar-target-url`, `--browser`, `--scholar-locale`, `--scholar-captcha-action`, `--scholar-captcha-timeout`, `--require-google-scholar`, `--min-delay`, `--max-delay`, `--s2-api-key-env`, `--export-legacy-csv`.
- `authors`: `--author-top-n`, `--max-author-profiles`, `--google-scholar-authors`, `--browser`, `--scholar-locale`, `--scholar-captcha-action`, `--scholar-captcha-timeout`, `--author-workers`, `--author-failure-policy`, `--canonical-author-metadata`, `--canonical-author-workers`, `--canonical-author-rps`, `--wiki-workers`, `--homepage-search-limit`, `--min-delay`, `--max-delay`, `--s2-api-key-env`, `--export-legacy-csv`.
- `download`: `--download-workers`, `--arxiv-fallback` / `--no-arxiv-fallback`, `--export-legacy-csv`.
- `analyze`: `--context-lines`, `--analysis-scope`, `--analyze-workers`, `--pdf-dir`, `--metadata`, `--export-legacy-csv`.

## Behavior

- Google Scholar is disabled by default for both discovery and author profiles. Enable discovery through `--platforms google-scholar,semantic-scholar,openalex,opencitations` or `--require-google-scholar`; enable author profiles separately with `--google-scholar-authors`.
- Semantic Scholar, OpenAlex, and OpenCitations/Crossref are enabled by default. Confirm actual use through dashboard source status, `run_notes`, and `papers.source_platforms`; require at least two sources to return records.
- When Google Scholar is explicitly enabled, Selenium uses `--scholar-captcha-action fail` by default, saves `scholar_debug/` evidence, records status, and lets other sources complete. Use `wait` only when a visible browser should remain open for manual verification.
- `find` runs all independent sources concurrently and waits at a barrier before merge/deduplication. Do not open multiple Google Scholar browser sessions for the same run; Google Scholar pagination stays serial so target matching, cited-by pagination, and captcha handling remain reliable.
- With the default `--source-failure-policy skip`, a source that returns 429/5xx, times out, exhausts quota, or triggers a captcha is recorded in `platform_errors` and skipped without blocking successful sources. Use `retry` only when completeness outweighs latency.
- When source caching is enabled, a skipped live source may contribute its most recent successful same-target snapshot. Record both the live error and `cached_fallback` status. Save successful source results independently after the discovery barrier so an intermittent source cannot erase a previously complete run.
- Google Scholar defaults to `--scholar-locale zh-CN` because cited-by pagination can expose different pages by locale; use `--scholar-locale en` only when needed.
- Google Scholar target pages can report a larger cited-by count than the public result pages expose. Read and preserve the reported count, but keep the collected-row count separate. Stop immediately at the known public pagination boundary when `start>=100` returns no rows; label the result `partial_google_result_cap` instead of wasting retries or pretending the hidden rows were collected.
- If Google Scholar target matching succeeds and some cited-by pages are already collected, a later pagination/captcha/driver interruption preserves the partial Google Scholar rows, records `partial_error` or `partial_captcha_blocked`, and continues downstream instead of discarding collected rows.
- Citing-paper rows from every source must include `citation_count`: parse the source count when present, otherwise write `0` instead of leaving the field empty.
- Semantic Scholar uses the Graph API and supports an optional API key. Leave `--s2-api-key` empty for anonymous requests, or use `--s2-api-key-env SEMANTIC_SCHOLAR_API_KEY` to enable authenticated requests later without changing workflows.
- Resolve Semantic Scholar targets in this order: DOI lookup as `DOI:<doi>`, then `paper/search/match`, then normalized title search. Handle `search/match` responses that return either a paper object or `{"data": [...]}`.
- Fetch Semantic Scholar citations from `/graph/v1/paper/{paperId}/citations` with nested `citingPaper.*` fields. Do not fetch citing papers by re-searching titles.
- For Semantic Scholar 429/5xx responses, read `Retry-After`, use backoff, and include status, URL, and a short response-body excerpt in `platform_errors.semantic-scholar`.
- `dedupe_key` in outputs always uses normalized title plus year. DOI, Semantic Scholar IDs, landing URLs, PDF URLs, OA PDF URLs, arXiv, and ACL links are internal duplicate-detection aliases.
- When multiple sources return the same citing paper, Google Scholar display fields take priority while Semantic Scholar and OpenAlex IDs, DOI, author IDs, institutions, and open-access metadata are retained.
- The `papers` sheet always includes both the display author string and structured author fields (`citing_authors_json`, `citing_author_ids`) when available. Structured authors preserve source-specific Semantic Scholar/OpenAlex IDs and OpenAlex institutions across source merges. Google-only rows may have only parsed names.
- Before author ranking, DOI-bearing rows are checked against Crossref author metadata. Canonical variants retain the source author ID. A supported hard conflict replaces the display name, records `originalName`, aliases, correction type, source/evidence/confidence, and moves the conflicting provider ID to `sourceAuthorId` instead of asserting that it belongs to the corrected person. Hard-conflict corrections bypass ordinary rank cutoffs for correct-name profile, honor, and homepage verification. Unsupported multi-position conflicts are left unchanged.
- The `authors` stage deduplicates authors by Semantic Scholar `authorId` first, then normalized name. It queries at most `--max-author-profiles` authors by default, prioritizing candidates with Semantic Scholar IDs, highly cited source papers, and repeated appearances. Semantic Scholar Author API lookups use `--author-workers` parallel workers.
- Author ranking, high-quality-author detection, dashboard author charts, and each paper's `top_author_*` fields exclude all target-paper authors, using `authorId` first and normalized names as a fallback. Per-paper representative authors prefer quality tier before personal citation count.
- Each row in the `papers` sheet records the highest-cited non-target author when one is available. If all authors are target authors, `top_author_status` is `all_authors_excluded_target`.
- Author citation counts prefer a high-confidence Google Scholar author profile. Accept Google Scholar only on exact-name matches with paper-list evidence from one of the current citing-paper titles. Otherwise record the low-confidence or ambiguous status and fall back to Semantic Scholar Author API metrics.
- Google Scholar author-profile lookup is opt-in through `--google-scholar-authors`. It remains serial because it has no stable public API, relies on profile work-list evidence to avoid homonym errors, and is sensitive to captcha/rate limiting. Existing cached Scholar profiles remain available when live queries are skipped.
- Author title/honor enrichment also follows the Google Scholar or Semantic Scholar homepage URL when present, including university/lab/personal pages. If no homepage URL is available, the expert-scope fallback uses a deep-search-style web search for likely personal/school profile pages (`--homepage-search-limit`, default 50), then validates that the page is the same person by cross-checking name, known affiliation, research interests, source context, and education/background evidence before accepting it. Deep-search pages must not be accepted on name alone: they need affiliation/research overlap, or an exact name plus education/background evidence on an academic profile URL. Unverified or same-name-only pages are rejected with `personal_homepage_rejection_reason` and are not shown as author homepage links. Verified evidence is shown in the dashboard as `personal_or_school_homepage`.
- Deep search uses exact-name queries targeted at the citing-paper affiliation, IEEE/ACM/AAAI Fellow status, national academies/Royal Society/Academia Europaea, and university/personal profiles. Authoritative society or academy pages receive a ranking boost, but identity still requires cross-evidence.
- OpenAlex institution evidence is retained per author and per citing paper. Major-company classification requires that structured authorship and company institution share the same citing record; supported companies include Google/DeepMind, NVIDIA, Microsoft, Meta, Amazon, Apple, Adobe, Intel, IBM, ByteDance/TikTok, Tencent, Alibaba, Huawei, Samsung, OpenAI, Waymo, Baidu, Kuaishou, and Megvii.
- Before rank-limited web enrichment, reverse-match every citing author against `references/verified-high-value-author-seeds.json`. Seed records contain independently verified official-profile evidence only; they never prove citing-paper authorship or target citation by themselves. Require a stable citing-author identity anchor, and require affiliation overlap for ambiguous names. This fallback must remain active when Semantic Scholar, Wikipedia, or Wikidata returns 429.
- Wikipedia/Wikidata enrichment checks priority non-target authors and merges with authoritative roster evidence when available. Classify verified authors as `elite_award`, `academy_member`, `ieee_fellow`, `society_fellow`, `major_company`, `high_impact`, `other_notable`, or `unverified`. `society_fellow` is reserved for independently verified ACM, AAAI, or IAPR Fellows and must not be relabeled as IEEE Fellow. The strict core accepts awards, academies, verified Fellows, and directly evidenced major-company authors. The default `high-impact` view adds a separately labeled metric-threshold supplement; ordinary professors, editors, conference chairs, and general society members do not qualify for the strict core. Preserve evidence and rejection reasons for auditability.
- PDF downloading uses parallel workers by default (`--download-workers 8`). A full run uses `--download-scope high-value`, so the evidence-stage download set is formed only after retained-author selection.
- PDF download only uses open/direct links, publisher metadata links, arXiv, or ACL Anthology. Do not use paywall bypasses.
- Analysis first locates the target paper's reference entry in each PDF, then reports only reliable body locations: verified numeric citation markers tied to that reference entry, or explicit target-name mentions. It writes reliable location and coverage data into the workbook and automatically generates a self-contained HTML dashboard.
- Citation contexts are classified as method, background, baseline/comparison, or dataset. Preserve the exact original context in the formal report; a positive label requires positive wording in that context.
- The `dashboard` command regenerates the HTML dashboard from `citation_report.xlsx`. If author sheets are absent, the dashboard hides author-specific panels.

## Outputs

The output directory contains:

- `pdf/high-value-citation-report.pdf` (or the path supplied with `--report-pdf`): required final user-facing report. Always render every page to images and inspect it before delivery.
- `citation_report.xlsx`: consolidated workbook with all table data.
- `citation_dashboard.html`: self-contained frontend dashboard with summary metrics, data-source status, source/download/coverage charts, researched citing-paper metadata table, highest-cited non-target author per paper with profile/homepage links, author impact ranking, author title/honor evidence table with Google Scholar/Semantic Scholar/personal homepage links and rejection diagnostics, notable-scholar citing-paper table when available, and reliable citation-location table.
- `author_profile_cache.json`: cached Google Scholar and Semantic Scholar author profile lookups.
- `crossref_author_metadata_cache.json`: versioned DOI author-list metadata used for reproducible name and affiliation reconciliation.
- `wikipedia_profile_cache.json`: cached Wikipedia/Wikidata enrichment lookups.
- `pdfs/`: downloaded open-access PDFs.
- Formal-report mode also produces a validated UTF-8 JSON source for the required Chinese PDF. Read `references/report-data-schema.md` before creating the JSON.

`citation_report.xlsx` sheets:

- `target`: resolved target-paper metadata and target authors.
- `papers`: one row per citing paper, merging discovery, download, analysis coverage, structured authors, and highest-cited non-target author fields.
- `paper_authors`: one row per citing-paper author, including order, target-author exclusion status, selected citation count, profile URLs, and personal/school homepage URLs.
- `authors`: non-target author ranking with Google Scholar/Semantic Scholar metrics, matching status, Wikipedia/Wikidata evidence, structured title/honor/role fields, notable status, and expert-query rejection diagnostics.
- `citation_locations`: reliable in-body citation locations and contexts.
- `downloaded_papers`: successfully downloaded or manually supplied papers, including local PDF path and final download URL.
- `download_failures`: papers not successfully downloaded, including landing URL, PDF candidates, expected manual path, and failure reason.
- `manual_download_todo`: failed download rows with candidate URLs, expected PDF paths, and `manual_pdf_path`.
- `notable_citations`: notable scholars and the citing papers in which they cite the target, including citation-location coverage, pages, markers, and a context sample when available.
- `run_notes`: run parameters and operational statistics, including Google Scholar rows/captcha/debug status and expert-query rejection summaries.

Legacy CSV/XLSX files such as `citing_papers.csv`, `download_manifest.csv`, `citation_locations_reliable.csv`, `author_candidates.csv`, and `notable_scholar_citing_papers.csv` are not generated by default. Use `--export-legacy-csv` only when a downstream debug workflow explicitly needs them.

## Script Reference

Use `python scripts/paper_citation_researcher.py <command> --help` for current flags.

Detailed workbook columns are documented in `references/output-schema.md`.
