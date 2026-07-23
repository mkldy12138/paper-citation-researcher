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

move_in_2d_source_names = [
    "Hsin-Ping Huang",
    "Yang Zhou",
    "Jui-Hsien Wang",
    "Difan Liu",
    "Feng Liu",
    "Mingzhu Yang",
    "Zhan Xu",
]
move_in_2d_canonical_names = [
    "Hsin-Ping Huang",
    "Yang Zhou",
    "Jui-Hsien Wang",
    "Difan Liu",
    "Feng Liu",
    "Ming-Hsuan Yang",
    "Zhan Xu",
]
source_entries = [
    {
        "name": name,
        "authorId": f"S2-{index}",
        "authorIdType": "semantic-scholar",
        "semanticAuthorId": f"S2-{index}",
        "institutions": [],
    }
    for index, name in enumerate(move_in_2d_source_names, 1)
]
crossref_metadata = {
    "title": ["Move-in-2D: 2D-Conditioned Human Motion Generation"],
    "author": [
        {
            "given": " ".join(name.split()[:-1]),
            "family": name.split()[-1],
            "affiliation": [{"name": "University of California, Merced"}] if index == 6 else [{"name": "Adobe Research"}],
        }
        for index, name in enumerate(move_in_2d_canonical_names, 1)
    ],
}
reconciled, corrections, status = MODULE.reconcile_crossref_author_entries(
    source_entries,
    crossref_metadata,
    "10.1109/CVPR52734.2025.02120",
    "Move-in-2D: 2D-Conditioned Human Motion Generation",
)
assert status == "reconciled"
assert len(corrections) == 1
assert reconciled[5]["name"] == "Ming-Hsuan Yang"
assert reconciled[5]["originalName"] == "Mingzhu Yang"
assert reconciled[5]["semanticAuthorId"] == ""
assert reconciled[5]["sourceAuthorId"] == "S2-6"
assert reconciled[5]["institutions"][0]["name"] == "University of California, Merced"
assert corrections[0]["correction_type"] == "hard_source_conflict"
assert reconciled[5]["nameCorrectionType"] == "hard_source_conflict"

reconciled_again, repeated_corrections, repeated_status = MODULE.reconcile_crossref_author_entries(
    reconciled,
    crossref_metadata,
    "10.1109/CVPR52734.2025.02120",
    "Move-in-2D: 2D-Conditioned Human Motion Generation",
)
assert repeated_status == "reconciled"
assert reconciled_again[5]["sourceAuthorId"] == "S2-6"
assert reconciled_again[5]["semanticAuthorId"] == ""
assert repeated_corrections[0]["rejected_source_author_id"] == "S2-6"

for source_name, canonical_name in (
    ("X. Qi", "Xiaojuan Qi"),
    ("Gul Varol", "Gül Varol"),
    ("Jeong Yeon Lee", "Jeongyeon Lee"),
    ("Kira L. Barton", "Kira Barton"),
):
    assert MODULE.author_name_token_equivalent(source_name, canonical_name)
assert not MODULE.author_name_token_equivalent("Mingzhu Yang", "Ming-Hsuan Yang")
assert not MODULE.author_name_token_equivalent("Yuyao Tang", "Yu-Ming Tang")

variant_entries = [dict(entry) for entry in source_entries]
variant_entries[0]["name"] = "X. Huang"
variant_metadata = dict(crossref_metadata)
variant_metadata["author"] = [dict(author) for author in crossref_metadata["author"]]
variant_metadata["author"][0] = {
    "given": "Hsin-Ping",
    "family": "Huang",
    "affiliation": [{"name": "Adobe Research"}],
}
variant_reconciled, variant_corrections, variant_status = MODULE.reconcile_crossref_author_entries(
    variant_entries,
    variant_metadata,
    "10.1109/CVPR52734.2025.02120",
    "Move-in-2D: 2D-Conditioned Human Motion Generation",
)
assert variant_status == "insufficient_coauthor_alignment"

variant_entries = [dict(entry) for entry in source_entries]
variant_entries[0]["name"] = "H. Huang"
variant_entries[5]["name"] = "Ming-Hsuan Yang"
variant_reconciled, variant_corrections, variant_status = MODULE.reconcile_crossref_author_entries(
    variant_entries,
    crossref_metadata,
    "10.1109/CVPR52734.2025.02120",
    "Move-in-2D: 2D-Conditioned Human Motion Generation",
)
assert variant_status == "reconciled"
assert variant_reconciled[0]["semanticAuthorId"] == "S2-1"
assert variant_reconciled[0]["nameCorrectionType"] == "canonical_name_variant"
assert variant_corrections[0]["correction_type"] == "canonical_name_variant"
assert MODULE.author_profile_priority(
    {"name_correction_types": "hard_source_conflict", "semantic_author_id": ""}
) > MODULE.author_profile_priority(
    {"name_correction_types": "", "semantic_author_id": "S2-STABLE"}
)
assert MODULE.select_s2_author_search_candidate(
    [
        {"name": "Mingcong Yang", "citationCount": 1456},
        {"name": "Ming-Hsuan Yang", "citationCount": 100},
    ],
    "Ming-Hsuan Yang",
)["name"] == "Ming-Hsuan Yang"
assert MODULE.select_s2_author_search_candidate(
    [{"name": "Mingcong Yang", "citationCount": 1456}],
    "Ming-Hsuan Yang",
) is None
assert MODULE.select_s2_author_search_candidate(
    [{"name": "David Yu", "citationCount": 10000}],
    "D. Yu",
) is None
assert not MODULE.cached_s2_author_identity_valid(
    {"name": "Ming-Hsuan Yang", "semantic_author_id": ""},
    {"name": "Mingcong Yang", "citationCount": 1456},
)


class DblpResponse:
    def __init__(self, payload=None, body=b"", url="https://dblp.org/test"):
        self.payload = payload or {}
        self.body = body
        self.url = url
        self.status_code = 200
        self.headers = {"content-type": "application/xml"}

    @property
    def ok(self):
        return True

    def json(self):
        return self.payload

    def iter_content(self, chunk_size=8192):
        for index in range(0, len(self.body), chunk_size):
            yield self.body[index:index + chunk_size]


class DblpSession:
    def get(self, url, **kwargs):
        if "search/author/api" in url:
            return DblpResponse(
                {
                    "result": {
                        "hits": {
                            "hit": [
                                {
                                    "info": {
                                        "author": "Ming-Hsuan Yang 0001",
                                        "notes": {
                                            "note": {
                                                "@type": "affiliation",
                                                "text": "University of California, Merced, EECS, USA",
                                            }
                                        },
                                        "url": "https://dblp.org/pid/79/3711",
                                    }
                                },
                                {
                                    "info": {
                                        "author": "Ming-Hsuan Yang 0002",
                                        "notes": {
                                            "note": {
                                                "@type": "affiliation",
                                                "text": "Arizona University, USA",
                                            }
                                        },
                                        "url": "https://dblp.org/pid/79/3711-2",
                                    }
                                },
                            ]
                        }
                    }
                },
                url=url,
            )
        person = (
            '<person key="homepages/79/3711">'
            '<url>https://faculty.ucmerced.edu/mhyang/</url>'
            '<url>https://orcid.org/0000-0003-4848-2304</url>'
            '<url>https://scholar.google.com/citations?user=p9-ohHsAAAAJ</url>'
            '</person>'
        ).encode("utf-8")
        return DblpResponse(body=person, url=url)


dblp_identity = MODULE.dblp_author_identity(
    DblpSession(),
    "Ming-Hsuan Yang",
    "University of California,Merced",
)
assert dblp_identity["status"] == "verified"
assert dblp_identity["author_url"] == "https://dblp.org/pid/79/3711"
assert dblp_identity["personal_homepage_url"] == "https://faculty.ucmerced.edu/mhyang/"
assert dblp_identity["orcid"].endswith("0000-0003-4848-2304")
assert MODULE.dblp_identity_cache_reusable(
    {"status": "verified", "enrichment_version": MODULE.DBLP_IDENTITY_VERSION}
)
assert MODULE.dblp_identity_cache_reusable(
    {
        "status": "error",
        "enrichment_version": MODULE.DBLP_IDENTITY_VERSION,
        "attempted_at": time.time(),
    }
)
assert not MODULE.dblp_identity_cache_reusable(
    {"status": "error", "enrichment_version": MODULE.DBLP_IDENTITY_VERSION}
)
wikidata_identity = MODULE.wikidata_corrected_identity(
    {
        "name": "Ming-Hsuan Yang",
        "name_correction_types": "hard_source_conflict",
        "source_affiliations": "University of California,Merced",
    },
    {
        "title": "Ming-Hsuan Yang",
        "wikidata_id": "Q87715520",
        "wikidata_affiliations": "University of California, Merced | Google DeepMind",
        "orcid": "https://orcid.org/0000-0003-4848-2304",
        "dblp_author_url": "https://dblp.org/pid/79/3711",
    },
)
assert wikidata_identity["confidence"] == "high"
assert wikidata_identity["dblp_author_url"].endswith("79/3711")


class HomepageResponse:
    def __init__(self, body, url):
        self.content = body
        self.url = url
        self.status_code = 200
        self.headers = {"content-type": "text/html"}
        self.encoding = "utf-8"

    @property
    def ok(self):
        return True

    @property
    def text(self):
        return self.content.decode(self.encoding, errors="replace")


class HomepageSession:
    def get(self, url, **kwargs):
        if url.endswith("bio.html"):
            body = (
                "Ming-Hsuan Yang is a Professor at the University of California, Merced. "
                "He is an IEEE Fellow, ACM Fellow, and AAAI Fellow."
            ).encode("utf-16")
            return HomepageResponse(body, url)
        body = (
            '<html><head><title>Ming-Hsuan Yang</title></head><body>'
            '<p>University of California, Merced</p>'
            '<a href="bio.html">Brief Biography</a>'
            '</body></html>'
        ).encode("utf-8")
        return HomepageResponse(body, url)


homepage_profile = MODULE.homepage_profile_summary(
    HomepageSession(),
    "https://faculty.ucmerced.edu/mhyang/",
    "Ming-Hsuan Yang",
    "University of California,Merced",
)
assert homepage_profile["homepage_identity_status"] == "verified"
assert homepage_profile["is_notable"] is True
assert "IEEE Fellow" in (
    homepage_profile.get("honors_awards", "")
    + homepage_profile.get("professional_memberships", "")
)
print("OK corrected-name DBLP identity and linked-biography verification")

unsafe_metadata = {
    "title": ["Move-in-2D: 2D-Conditioned Human Motion Generation"],
    "author": [
        {"given": "Different", "family": f"Person{index}", "affiliation": [{"name": "Unknown"}]}
        for index in range(1, 8)
    ],
}
unchanged, unsafe_corrections, unsafe_status = MODULE.reconcile_crossref_author_entries(
    source_entries,
    unsafe_metadata,
    "10.1109/CVPR52734.2025.02120",
    "Move-in-2D: 2D-Conditioned Human Motion Generation",
)
assert unsafe_status == "insufficient_coauthor_alignment"
assert not unsafe_corrections
assert unchanged[5]["name"] == "Mingzhu Yang"
print("OK DOI author-order reconciliation and unsafe-correction rejection")


async def failed_crossref_metadata(items, workers, failure_policy, requests_per_second):
    return {
        index: {"_metadata_error": "429 Too Many Requests"}
        for index, _ in enumerate(items)
    }


original_crossref_metadata = MODULE.async_crossref_metadata
MODULE.async_crossref_metadata = failed_crossref_metadata
try:
    with tempfile.TemporaryDirectory() as cache_root:
        failed_paper = MODULE.pd.DataFrame(
            [
                {
                    "dedupe_key": "failed-crossref-paper",
                    "citing_title": "Failed Crossref Paper",
                    "doi": "10.1000/retry-me",
                    "citing_authors": "First Author, Second Author",
                    "citing_authors_json": json.dumps(
                        [
                            {"name": "First Author", "institutions": []},
                            {"name": "Second Author", "institutions": []},
                        ]
                    ),
                }
            ]
        )
        _, failure_stats = MODULE.canonicalize_citing_authors(cache_root, failed_paper)
        cache = json.loads((Path(cache_root) / "crossref_author_metadata_cache.json").read_text(encoding="utf-8"))
        assert failure_stats["queried_dois"] == 1
        assert "10.1000/retry-me" not in cache["records"]
finally:
    MODULE.async_crossref_metadata = original_crossref_metadata
print("OK transient Crossref author-metadata failures remain retryable")
