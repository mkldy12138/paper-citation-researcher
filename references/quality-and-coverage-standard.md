# High-Coverage Citation Research Standard

Use this standard when the user requests information volume comparable to a detailed AMiner-style citation PDF.

## Benchmark

The reference GPUSQ report contains 72 reported citations, 15 detailed author records, and 8 authors with interpretable body-context assessments. Match its investigation depth, not its inclusion mistakes: do not add ordinary high-citation authors unless they independently qualify through an allowed honor or major-company category.

## Discovery

1. Query Semantic Scholar, OpenAlex, and OpenCitations/Crossref by default. Add Google Scholar only when the user explicitly accepts browser verification or requires its reported count.
2. Require at least two successful citation sources. Record source-specific reported counts, collected rows, failures, and retrieval dates.
3. Continue pagination to the platform limit. Deduplicate by normalized title/year plus DOI and stable IDs.
4. Expand every collected citing paper to every author. Do not limit candidate discovery to first authors or the highest-cited papers.
5. Run at least two candidate-enrichment passes:
   - pass 1: stable author IDs, affiliations, honor rosters, and company institutions;
   - pass 2: reverse-match complete academy/Fellow/award rosters and search unresolved high-priority names.
6. Stop only after a saturation pass adds no new verified high-value person, or document the remaining limitation.

## Allowed Main Categories

- Turing Award and comparably selective international prize recipients;
- national academy/engineering academy members and Fellows of the Royal Society;
- verified IEEE Fellows, plus ACM/AAAI/IAPR Fellows when materially relevant;
- authors affiliated on the citing paper with a major international technology company;
- other exceptionally selective awards only with an authoritative award source.

Do not use h-index alone as admission evidence. Keep h-index and citation counts as descriptive fields after identity resolution.

## Five-Claim Verification

Verify each retained row as five separate claims:

1. the person authored the named citing paper;
2. the citing paper cites the exact target paper;
3. the person holds the stated honor or paper-time company affiliation;
4. the homepage/profile belongs to the same person;
5. the reported assessment accurately paraphrases the citing paper's body context.

Assign `supported`, `partially-supported`, `uncertain`, or `unsupported` to each claim. Main tables may contain only rows whose claims 1-3 are supported. A positive evaluation requires claim 5 to be supported; otherwise label the record as method use/comparison, reference-list-only, or full text unavailable.

## Coverage Metrics

Record these values in `coverage` within the formal-report JSON:

- `reported_citation_count_max`
- `discovered_unique_citing_papers`
- `source_success_count` and `source_counts`
- `citing_papers_with_authors`
- `unique_citing_authors`
- `authors_profiled`
- `high_value_candidates_reviewed`
- `retained_scholars`
- `retained_company_authors`
- `retained_with_homepage`
- `retained_with_verified_context`
- `fulltext_attempted` and `fulltext_acquired`
- `positive_contexts`
- `search_passes`
- `new_verified_people_last_pass`
- `unresolved_candidates`

Treat a discovered/report-count ratio below 0.65, fewer than two successful sources, missing author expansion, or a nonzero final-pass yield as incomplete. Do not describe an incomplete run as exhaustive.

For detailed formal reports, at least 50% of retained people should have verified body context. Every verified context must retain the original passage, one role from `method`, `background`, `baseline`, or `dataset`, and a specific conservative Chinese technical explanation. An automatically generated role-only sentence is a draft, not a final assessment.

## Output Density

For every retained person show: name, all verified high-value titles, h-index when identity-matched, personal citation count when source-matched, institution, exact citing-paper title, venue/year, citing-paper citation count, target-citation frequency, homepage, evidence URLs, confidence, five-claim verdicts, full body context when available, and a conservative Chinese assessment.

Keep one person per detail block. Separate scholars from company authors and deduplicate people across categories while preserving all qualifying labels.
