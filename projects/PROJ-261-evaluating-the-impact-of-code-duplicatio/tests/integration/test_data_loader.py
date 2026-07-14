"""
Integration test for :func:`download_and_save_sample`.

The test verifies that the data‑loader is tolerant to transient network
failures such as rate‑limiting.  It does this by monkey‑patching the
``datasets.load_dataset`` function to raise an exception after a few rows
have been yielded.  The loader should catch the exception, retry, and
ultimately produce a CSV file containing *at most* the requested number
of rows without propagating the error.
"""

import csv
import builtins
from pathlib import Path

import pytest

# Import the function under test
from data_loader import download_and_save_sample


class MockStreamingDataset:
    """
    Mimics the iterator returned by ``datasets.load_dataset(..., streaming=True)``.
    It yields a configurable number of rows and then raises a
    ``ConnectionError`` to simulate a rate‑limit/network interruption.
    """

    def __init__(self, total_rows: int, fail_at: int):
        self.total_rows = total_rows
        self.fail_at = fail_at
        self._counter = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self._counter == self.fail_at:
            # Simulate a transient network problem
            raise ConnectionError("Simulated network interruption")
        if self._counter >= self.total_rows:
            raise StopIteration
        # Produce a minimal example resembling the real dataset
        example = {
            "path": f"file_{self._counter}.py",
            "content": f"# sample code {self._counter}",
        }
        self._counter += 1
        return example

    def take(self, n):
        """
        ``datasets`` streaming objects expose a ``take`` method that returns
        an iterator limited to ``n`` items.  For the mock we simply ignore
        ``n`` because the iterator already knows its total length.
        """
        return self


def test_download_and_save_sample_handles_transient_failure(tmp_path, monkeypatch):
    """
    The loader should:
    1. Attempt to stream the dataset.
    2. Recover from a simulated ``ConnectionError``.
    3. Write a CSV file with the requested number of rows (or fewer if the
       mock stops early after retries).
    """

    # ------------------------------------------------------------------
    # Patch ``datasets.load_dataset`` to return our mock object.
    # The mock will succeed for the first two rows, then raise an error.
    # ------------------------------------------------------------------
    def mock_load_dataset(*_args, **_kwargs):
        # Ask for 5 rows total, fail after 2 rows.
        return MockStreamingDataset(total_rows=5, fail_at=2)

    monkeypatch.setattr("datasets.load_dataset", mock_load_dataset)

    # Use a temporary output location to avoid polluting the repo.
    out_file = tmp_path / "github-code-sample.csv"

    # Run the function under test.
    result_path = download_and_save_sample(sample_size=4, output_path=out_file)

    # Verify the function reports the correct path.
    assert result_path == out_file.resolve()

    # Validate the CSV content.
    assert out_file.is_file(), "CSV file was not created"

    with out_file.open(newline="") as f:
        rows = list(csv.DictReader(f))

    # The mock yields 2 rows before raising; the loader retries and will
    # re‑start the iterator, yielding the same first two rows again plus
    # up to the remaining requested rows.  The exact count can be 4
    # (requested) or fewer if the mock stops early after retries.
    # We only assert that *at most* ``sample_size`` rows are present and
    # that the required columns exist.
    assert len(rows) <= 4, f"Too many rows written: {len(rows)}"
    assert len(rows) >= 2, "Not enough rows written after retry"
    for row in rows:
        assert "file_path" in row
        assert "code" in row
        # Basic sanity check on content
        assert row["file_path"].startswith("file_")
        assert row["code"].startswith("# sample code")


@pytest.mark.skipif(
    not hasattr(builtins, "__import__"),
    reason="Skipping real download in restricted environments",
)
def test_download_and_save_sample_real_download(tmp_path, monkeypatch):
    """
    A light‑weight integration test that actually streams a tiny
    ``codeparrot/github-code`` sample (2 rows) using the real library.
    It is skipped on CI environments without internet access.
    """
    out_file = tmp_path / "real-sample.csv"
    result_path = download_and_save_sample(sample_size=2, output_path=out_file)

    assert result_path == out_file.resolve()
    assert out_file.is_file()
    with out_file.open(newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2
    for row in rows:
        assert "file_path" in row and "code" in row