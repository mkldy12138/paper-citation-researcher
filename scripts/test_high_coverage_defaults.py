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
assert args.max_papers == 1000
assert args.max_author_profiles == 1000
assert args.author_top_n == 100
assert args.homepage_search_limit == 250

print("OK high-coverage defaults")
