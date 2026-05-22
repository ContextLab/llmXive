from llmxive.librarian.dataset_sources import DatasetCandidate, search_huggingface


def test_huggingface_search_returns_real_candidates():
    cands = search_huggingface("QM9", limit=5)
    assert cands, "expected >=1 HF dataset candidate for QM9"
    c = cands[0]
    assert isinstance(c, DatasetCandidate)
    assert c.source == "huggingface"
    assert c.hf_id and "/" in c.hf_id            # e.g. "n0w0f/qm9-csv" style id
    assert c.url.startswith("https://huggingface.co/datasets/")
