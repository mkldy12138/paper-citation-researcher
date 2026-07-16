import argparse
import json
from pathlib import Path


REQUIRED_COVERAGE = (
    "reported_citation_count_max",
    "discovered_unique_citing_papers",
    "source_success_count",
    "source_counts",
    "citing_papers_with_authors",
    "unique_citing_authors",
    "authors_profiled",
    "high_value_candidates_reviewed",
    "retained_scholars",
    "retained_company_authors",
    "retained_with_homepage",
    "retained_with_verified_context",
    "fulltext_attempted",
    "fulltext_acquired",
    "positive_contexts",
    "search_passes",
    "new_verified_people_last_pass",
    "unresolved_candidates",
)


def number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def main():
    parser = argparse.ArgumentParser(description="Audit citation-report coverage and evidence density")
    parser.add_argument("report_json")
    parser.add_argument("--strict", action="store_true", help="Fail on incomplete coverage instead of emitting warnings")
    args = parser.parse_args()

    data = json.loads(Path(args.report_json).read_text(encoding="utf-8"))
    coverage = data.get("coverage") or {}
    errors = []
    warnings = []
    for key in REQUIRED_COVERAGE:
        if key not in coverage:
            errors.append(f"coverage.{key} is required")

    scholars = data.get("scholars", [])
    companies = data.get("companies", [])
    retained = scholars + companies
    if int(number(coverage.get("retained_scholars"))) != len(scholars):
        errors.append("coverage.retained_scholars does not match scholars length")
    if int(number(coverage.get("retained_company_authors"))) != len(companies):
        errors.append("coverage.retained_company_authors does not match companies length")

    reported = number(coverage.get("reported_citation_count_max"))
    discovered = number(coverage.get("discovered_unique_citing_papers"))
    recall = discovered / reported if reported else 1.0
    if reported and recall < 0.65:
        warnings.append(f"discovery coverage is only {recall:.1%} ({int(discovered)}/{int(reported)})")
    if number(coverage.get("source_success_count")) < 2:
        warnings.append("fewer than two citation sources returned records")
    if number(coverage.get("citing_papers_with_authors")) < discovered * 0.9:
        warnings.append("fewer than 90% of discovered citing papers have expanded authors")
    if number(coverage.get("search_passes")) < 2:
        warnings.append("fewer than two candidate-enrichment passes were completed")
    if number(coverage.get("new_verified_people_last_pass")) > 0:
        warnings.append("the final pass still found new verified people; saturation was not reached")

    homepage_count = sum(1 for row in retained if row.get("homepage"))
    context_count = sum(
        1
        for row in retained
        if any(p.get("context_status") == "verified" for p in row.get("citing_papers", []))
    )
    if retained and homepage_count / len(retained) < 0.5:
        warnings.append("fewer than 50% of retained people have verified homepages")
    if retained and context_count / len(retained) < 0.35:
        warnings.append("fewer than 35% of retained people have verified body context")

    if errors or (args.strict and warnings):
        for item in errors:
            print(f"ERROR: {item}")
        for item in warnings:
            print(f"{'ERROR' if args.strict else 'WARNING'}: {item}")
        return 1

    for item in warnings:
        print(f"WARNING: {item}")
    print(
        f"OK: {int(discovered)} citing papers, {len(scholars)} scholars, "
        f"{len(companies)} company authors, {context_count} verified contexts"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
