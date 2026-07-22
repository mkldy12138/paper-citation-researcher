# MotionGPT Benchmark Lessons

Benchmark file: `MotionGPT_ Human Mot_2026年07月14日17时48分00秒.pdf`.

## Observed coverage

- 31 A4 pages.
- Pages 1-4 contain target metadata and a 20-row overview representing 19 displayed names; two rows named Lei Zhang have different institutions and must remain separate until identity resolution.
- Pages 5-31 expand one author at a time with the citing-paper title, citing-paper authors, venue/year, highlighted original context, citation type, and a Chinese technical paraphrase.
- The overview mixes strict elite authors, Fellows, major-company authors, and high-impact scholars. Examples include Li Fei-Fei, Jitendra Malik, Richard Hartley, Dacheng Tao, NVIDIA author Tsung-Yi Lin, and TikTok author Jiashi Feng.

## What to reproduce

1. Expand every citing-paper author before ranking; do not inspect only first/last authors.
2. Preserve structured institutions from OpenAlex and merge them with Semantic Scholar author IDs by normalized name and paper identity.
3. Maintain two report layers:
   - strict high-value: elite prizes, academies, verified IEEE Fellows, and directly evidenced major-company authors;
   - high-impact supplement: identity-verified authors with at least 50,000 citations or h-index at least 100.
4. Run targeted deep searches for each priority author: exact name plus affiliation, IEEE/ACM/AAAI Fellow, national academy/Royal Society/Academia Europaea, and personal or university homepage.
5. For every retained author, keep the exact citing-paper title and, when a PDF is available, original citation context plus a conservative Chinese paraphrase.
6. Measure coverage by unique retained people, retained citation records, homepage coverage, honor-evidence coverage, company-evidence coverage, and citation-context coverage.
7. Use one person per detail block. Under that person, list every named citing paper separately; never merge several people into one prose item.
8. Download retained high-value citing papers after author selection, then preserve the exact body passage and classify its role as method, background, baseline/comparison, or dataset.
9. Present the original passage before the Chinese technical explanation. The explanation must describe what the citing paper says about the target contribution, not merely state that a citation exists.

## What not to copy

- The benchmark itself warns that some content is AI-generated and may be inaccurate.
- It contains extraction or source errors such as `Rnichard Hartley`, duplicated `IEEE Fellow`, and ambiguous same-name rows.
- Do not accept h-index, name-only matches, or company platform alone as identity proof.
- Do not treat a neutral baseline/background mention as a positive assessment.
- Do not copy titles or honors from the benchmark without independent verification, unless the user explicitly marks the source as manually verified.

## Quality target

Match the benchmark's evidence density, not its unsupported certainty. A comparable result should have one author per row, exact citing-paper title, verified titles/honors, direct company-affiliation evidence, profile/homepage, confidence label, and citation context where available. In strict mode, fewer than two enrichment passes, a nonzero final-pass yield, fewer than 50% of retained people with verified body context, or missing per-context role/original text/Chinese explanation fails the quality gate.

Report benchmark recall at three levels: normalized-name presence, affiliation-resolved identity, and full VHAR evidence. Never count a unique same-name row as identity-resolved when the reference provides an affiliation and the collected profile has no matching affiliation evidence.
