import importlib.util
import json
import tempfile
import time
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("paper_citation_researcher.py")
SPEC = importlib.util.spec_from_file_location("paper_citation_researcher", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code
        self.headers = {}
        self.reason = "Too Many Requests" if status_code == 429 else "OK"
        self.url = "https://example.test/api"
        self.text = "rate limited" if status_code == 429 else ""

    @property
    def ok(self):
        return 200 <= self.status_code < 400

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, links):
        self.links = links

    def get(self, *args, **kwargs):
        return FakeResponse(self.links)


links = [
    {"oci": f"oci-{index}", "citing": f"10.1000/example-{index}", "creation": "2026"}
    for index in range(8)
]


def fake_metadata(session, doi):
    time.sleep(0.05)
    index = int(doi.rsplit("-", 1)[-1])
    return {
        "title": [f"Paper {index}"],
        "container-title": ["Test Venue"],
        "published": {"date-parts": [[2026]]},
        "author": [{"given": "Author", "family": str(index)}],
        "URL": f"https://doi.org/{doi}",
        "is-referenced-by-count": index,
    }


original = MODULE.crossref_citing_metadata
MODULE.crossref_citing_metadata = fake_metadata
try:
    started = time.monotonic()
    rows = MODULE.opencitations_fetch_citations(
        FakeSession(links),
        {"DOI": "10.1000/target"},
        limit=8,
        metadata_workers=4,
        use_async_http=False,
    )
    elapsed = time.monotonic() - started
finally:
    MODULE.crossref_citing_metadata = original

assert len(rows) == 8
assert [row["citing_title"] for row in rows] == [f"Paper {index}" for index in range(8)]
assert elapsed < 0.30, f"metadata fan-out appears serial: {elapsed:.3f}s"
assert json.loads(rows[7]["citing_authors_json"])[0]["name"] == "Author 7"

print(f"OK concurrent metadata barrier ({elapsed:.3f}s)")


class RateLimitedSession:
    def __init__(self):
        self.calls = 0

    def get(self, *args, **kwargs):
        self.calls += 1
        return FakeResponse({}, status_code=429)


rate_limited = RateLimitedSession()
started = time.monotonic()
response = MODULE.s2_get(
    rate_limited,
    "https://example.test/api",
    {},
    max_retries=1,
)
skip_elapsed = time.monotonic() - started
assert response.status_code == 429
assert rate_limited.calls == 1
assert skip_elapsed < 0.05, f"skip policy unexpectedly waited: {skip_elapsed:.3f}s"
print(f"OK fast 429 skip ({skip_elapsed:.3f}s)")


with tempfile.TemporaryDirectory() as cache_root:
    cache_output = Path(cache_root)
    cached_result = (
        "semantic-scholar",
        {"title": "Target paper"},
        [{"citing_title": "Cached citing paper", "source_platforms": "semantic-scholar"}],
        {"rows": 1, "status": "ok", "elapsed_seconds": 0.1},
    )
    MODULE.save_discovery_cache(cache_output, "Target paper", cached_result)
    fallback = MODULE.load_discovery_cache(
        cache_output,
        "Target paper",
        "semantic-scholar",
        max_age_hours=24,
        source_error="429 Too Many Requests",
    )
    assert fallback is not None
    assert fallback[2][0]["citing_title"] == "Cached citing paper"
    assert fallback[3]["status"] == "cached_fallback"
    assert fallback[3]["live_source_error"] == "429 Too Many Requests"
    assert MODULE.load_discovery_cache(
        cache_output,
        "Different target",
        "semantic-scholar",
        max_age_hours=24,
        source_error="429",
    ) is None
print("OK source cache fallback")

assert MODULE.is_transient_s2_error("Semantic Scholar author lookup failed: 429 Too Many Requests")
assert MODULE.is_transient_s2_error("connection timeout")
assert not MODULE.is_transient_s2_error("Semantic Scholar author lookup failed: 404 Not Found")
print("OK Semantic Scholar circuit-break classification")

company_papers = MODULE.pd.DataFrame([
    {
        "citing_title": "A structured company citation",
        "citing_authors": "Test Author",
        "citing_authors_json": json.dumps([
            {
                "name": "Test Author",
                "authorId": "A123",
                "authorIdType": "openalex",
                "institutions": [{"name": "NVIDIA Research", "type": "company"}],
            }
        ]),
        "publication_year": 2026,
        "citation_count": 10,
        "source_platforms": "openalex",
    }
])
company_candidates, _ = MODULE.collect_author_candidates_from_papers(company_papers)
assert len(company_candidates) == 1
company_author = company_candidates[0]
assert company_author["semantic_author_id"] == ""
assert company_author["openalex_author_id"] == "A123"
assert company_author["source_company_affiliations"] == "NVIDIA"
assert "A structured company citation" in company_author["company_affiliation_evidence"]
tier, _, accepted = MODULE.classify_author_quality(
    "",
    "verified_by_authorship",
    0,
    0,
    False,
    company_author["source_company_affiliations"],
)
assert (tier, accepted) == ("major_company", True)
print("OK structured major-company authorship evidence")

merged_company_rows = MODULE.merge_records([
    {
        "source_platforms": "semantic-scholar",
        "source_record_ids": "s2:paper-1",
        "citing_title": "Merged structured citation",
        "publication_year": 2026,
        "citing_authors_json": json.dumps([
            {
                "name": "Test Author",
                "authorId": "S2A1",
                "authorIdType": "semantic-scholar",
                "semanticAuthorId": "S2A1",
                "institutions": [],
            }
        ]),
    },
    {
        "source_platforms": "openalex",
        "source_record_ids": "openalex:W1",
        "citing_title": "Merged structured citation",
        "publication_year": 2026,
        "citing_authors_json": json.dumps([
            {
                "name": "Test Author",
                "authorId": "OAA1",
                "authorIdType": "openalex",
                "openalexAuthorId": "OAA1",
                "institutions": [{"name": "NVIDIA Research", "type": "company"}],
            }
        ]),
    },
])
merged_authors = MODULE.parse_author_json(merged_company_rows[0]["citing_authors_json"])
assert merged_authors[0]["semanticAuthorId"] == "S2A1"
assert merged_authors[0]["openalexAuthorId"] == "OAA1"
assert merged_authors[0]["institutions"][0]["name"] == "NVIDIA Research"
print("OK cross-source structured author merge")

same_name_papers = MODULE.pd.DataFrame([
    {
        "citing_title": f"Paper {index}",
        "publication_year": 2026,
        "citation_count": 1,
        "source_platforms": "semantic-scholar",
        "citing_authors_json": json.dumps([
            {
                "name": "Lei Zhang",
                "authorId": author_id,
                "authorIdType": "semantic-scholar",
                "semanticAuthorId": author_id,
                "institutions": [],
            }
        ]),
    }
    for index, author_id in enumerate(("S2-LEI-1", "S2-LEI-2"), 1)
])
same_name_candidates, _ = MODULE.collect_author_candidates_from_papers(same_name_papers)
assert len(same_name_candidates) == 2
assert {item["author_key"] for item in same_name_candidates} == {"s2:S2-LEI-1", "s2:S2-LEI-2"}
print("OK same-name stable-ID disambiguation")

motiongpt_aliases = MODULE.target_title_aliases({"title": "MotionGPT: Human Motion as a Foreign Language"})
assert "MotionGPT" in motiongpt_aliases
assert MODULE.classify_citation_role("We use MotionGPT as our base model.") == "method"
assert MODULE.classify_citation_role("We compare against MotionGPT as a baseline.") == "baseline"
assert MODULE.classify_citation_role("The dataset follows MotionGPT annotations.") == "dataset"
assert MODULE.classify_citation_role("Recent work includes MotionGPT [12].") == "background"
print("OK dynamic target aliases and citation-role classification")
