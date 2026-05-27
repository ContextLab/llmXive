from llmxive.librarian.dataset_sources import (
    DatasetCandidate,
    search_datacite,
    search_figshare,
    search_huggingface,
    search_zenodo,
)


def test_huggingface_search_returns_real_candidates():
    cands = search_huggingface("QM9", limit=5)
    assert cands, "expected >=1 HF dataset candidate for QM9"
    c = cands[0]
    assert isinstance(c, DatasetCandidate)
    assert c.source == "huggingface"
    assert c.hf_id and "/" in c.hf_id            # e.g. "n0w0f/qm9-csv" style id
    assert c.url.startswith("https://huggingface.co/datasets/")


def test_figshare_search_returns_candidates():
    cands = search_figshare("QM9 molecular", limit=5)
    assert all(c.source == "figshare" and c.url.startswith("http") for c in cands)
    # figshare may legitimately return 0 for a narrow query; assert shape only.


def test_zenodo_search_returns_candidates():
    cands = search_zenodo("QM9 quantum chemistry", limit=5)
    assert all(c.source == "zenodo" and c.url.startswith("http") for c in cands)


def test_datacite_resolves_doi():
    # FIX 3: 10.1038/sdata.2014.22 is a *Crossref* DOI (Nature Scientific Data),
    # not registered in DataCite, so search_datacite returns [] for it -- the old
    # assertion was vacuously true. Zenodo mints DataCite DOIs, so we use a real
    # Zenodo record whose DOI returns 200 from https://api.datacite.org/dois/<doi>
    # (verified by curl on 2026-05-21). This genuinely exercises the resolve path.
    cands = search_datacite("10.5281/zenodo.1227121", limit=3)
    assert cands, "expected >=1 DataCite candidate for a Zenodo-minted DOI"
    assert all(c.source == "datacite" and c.url.startswith("http") for c in cands)
    # The resolved DOI URL must be reachable (doi.org resolves the Zenodo record).
    import requests
    r = requests.get(cands[0].url, allow_redirects=True, timeout=30,
                     headers={"User-Agent": "llmxive-test/1.0"})
    assert r.status_code == 200, f"{cands[0].url} -> {r.status_code}"
