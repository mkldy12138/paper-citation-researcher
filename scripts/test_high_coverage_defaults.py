import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("paper_citation_researcher.py")
SPEC = importlib.util.spec_from_file_location("paper_citation_researcher", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


parser = MODULE.build_parser()
args = parser.parse_args([
    "run",
    "--paper",
    "Example Paper",
    "--output",
    "out",
])

assert args.platforms == "google-scholar,semantic-scholar,openalex,opencitations"
assert args.minimum_source_success == 2
assert args.find_workers == 4
assert args.metadata_workers == 12
assert args.metadata_rps == 5.0
assert args.async_http is True
assert args.source_failure_policy == "skip"
assert args.source_cache is True
assert args.source_cache_max_age_hours == 168.0
assert args.scholar_target_url == ""
assert args.scholar_captcha_action == "fail"
assert args.max_papers == 1000
assert args.max_author_profiles == 1000
assert args.author_top_n == 100
assert args.homepage_search_limit == 250
assert args.author_workers == 8
assert args.author_failure_policy == "skip"
assert args.wiki_workers == 4
assert args.download_workers == 8
assert args.analyze_workers == 4
assert args.author_quality_scope == "high-impact"
assert args.download_scope == "high-value"
assert args.formal_report is True
assert args.strict_report is False

print("OK high-coverage defaults")
