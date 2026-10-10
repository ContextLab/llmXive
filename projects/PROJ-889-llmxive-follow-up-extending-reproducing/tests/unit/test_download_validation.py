"""
Unit tests for the download validation logic (T013b).
The tests mock the network‑related functions to avoid real I/O.
"""

import builtins
import pytest

from download_cherrl_logs import verify_arxiv_source, download_from_huggingface

# ----------------------------------------------------------------------
# verify_arxiv_source tests
# ----------------------------------------------------------------------
def test_verify_arxiv_source_success():
    # The expected URL is defined in the implementation.
    from download_cherrl_logs import EXPECTED_ARXIV_URL
    assert verify_arxiv_source(EXPECTED_ARXIV_URL) is True

def test_verify_arxiv_source_failure():
    with pytest.raises(ValueError) as excinfo:
        verify_arxiv_source("https://invalid.example.com")
    assert "Invalid source URL" in str(excinfo.value)

# ----------------------------------------------------------------------
# download_from_huggingface tests (mocked)
# ----------------------------------------------------------------------
class DummySplit:
    """A minimal iterator that mimics a streaming split."""
    def __init__(self, columns, rows):
        self.columns = columns
        self.rows = rows
        self._iter = iter(rows)

    def __iter__(self):
        return self

    def __next__(self):
        return next(self._iter)

class DummyDatasetDict(dict):
    """Mimics the object returned by ``load_dataset(..., split=None)``."""
    pass

def dummy_load_dataset(*args, **kwargs):
    """
    Mock ``datasets.load_dataset``.
    Returns a dummy dataset dict with a single valid split.
    """
    split_name = "valid_split"
    columns = ["J_biased", "J_unbiased", "J_gold", "seed_id"]
    rows = [
        {col: i for col in columns}
        for i in range(5)
    ]
    dummy_split = DummySplit(columns, rows)
    if kwargs.get("split") is None:
        # Called with split=None – return a dict of split names.
        return DummyDatasetDict({split_name: dummy_split})
    else:
        # Return the actual split iterator.
        return dummy_split

def test_download_from_huggingface_success(monkeypatch, tmp_path):
    # Patch the real ``load_dataset`` with our dummy implementation.
    monkeypatch.setattr("download_cherrl_logs.load_dataset", dummy_load_dataset)

    output_path = tmp_path / "out.csv"
    result_path = download_from_huggingface(
        dataset_id="dummy/dataset",
        output_path=output_path,
    )
    # The function should return the path we supplied.
    assert result_path == output_path
    # Verify that the CSV file was created and contains the expected header.
    content = output_path.read_text()
    header = content.splitlines()[0].strip()
    assert set(header.split(",")) == {"J_biased", "J_unbiased", "J_gold", "seed_id"}

def test_download_from_huggingface_no_valid_split(monkeypatch):
    # Create a dummy ``load_dataset`` that returns a split lacking required columns.
    def bad_load_dataset(*args, **kwargs):
        split = DummySplit(columns=["foo", "bar"], rows=[{"foo": 1, "bar": 2}])
        if kwargs.get("split") is None:
            return DummyDatasetDict({"bad_split": split})
        return split

    monkeypatch.setattr("download_cherrl_logs.load_dataset", bad_load_dataset)

    with pytest.raises(SystemExit) as excinfo:
        download_from_huggingface(dataset_id="dummy/bad")
    # Exit code 2 indicates a loud failure as specified.
    assert excinfo.value.code == 2

# Note: The actual network call is never performed; the tests rely on the
# mocked ``load_dataset`` function. This satisfies the requirement that the
# validation logic works correctly while keeping the CI fast and deterministic.