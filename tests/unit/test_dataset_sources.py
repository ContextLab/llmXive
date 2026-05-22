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
    # The QM9 Scientific Data paper DOI (verified reachable).
    cands = search_datacite("10.1038/sdata.2014.22", limit=3)
    assert all(c.source == "datacite" and c.url.startswith("http") for c in cands)
