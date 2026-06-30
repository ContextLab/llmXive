"""Integration test for the data‑loader.

The test verifies that ``download_and_save_sample`` creates the expected
CSV file without raising an exception.
"""

import os
from pathlib import Path

import pytest

from code.data_loader import download_and_save_sample

@pytest.mark.integration
def test_download_and_save_sample_creates_file(tmp_path, monkeypatch):
    """Run the loader in a temporary directory and check output."""
    # Redirect the output path to a temporary location.
    tmp_csv = tmp_path / "github-code-sample.csv"
    monkeypatch.setattr(
        "code.data_loader.Path",
        lambda *parts: tmp_csv if parts == ("data", "raw", "github-code-sample.csv") else Path(*parts),
    )

    # Execute the download (it will stream a very small sample because of the
    # byte‑budget logic – this keeps the test fast and deterministic).
    result_path = download_and_save_sample()

    assert result_path == tmp_csv
    assert tmp_csv.is_file()
    # Basic sanity check – the CSV must have at least a header row.
    with tmp_csv.open() as f:
        header = f.readline()
        assert "content" in header.lower()