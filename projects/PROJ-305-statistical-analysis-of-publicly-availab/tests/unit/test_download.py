"""
Unit test for the VAERS download script (T002).
Ensures that after execution the expected files exist,
that the checksum line is present, and that the downloaded
parquet file is non‑empty.
"""

import os
from pathlib import Path

import pytest

from llmxive_toolkit import paths

# The script is executed as part of the task artefact; we import the
# public function to verify its behaviour without re‑running the whole
# download (which would hit the network again during the test suite).
# However, the test only checks side‑effects that should already be
# present after the task execution.

@pytest.fixture(scope="module")
def download_outputs():
    """Yield paths that should have been created by the download step."""
    parquet = paths.data("raw", "vaers_2020_2023.parquet")
    checksum = paths.data("checksums.txt")
    summary = paths.data("results", "download_summary.txt")
    # Ensure the files exist – the task runner will have executed the
    # script before this test runs.
    assert parquet.is_file(), f"Parquet file missing: {parquet}"
    assert checksum.is_file(), f"Checksum file missing: {checksum}"
    assert summary.is_file(), f"Summary file missing: {summary}"
    return {"parquet": parquet, "checksum": checksum, "summary": summary}

def test_parquet_non_empty(download_outputs):
    parquet_path = download_outputs["parquet"]
    assert parquet_path.stat().st_size > 0, "Downloaded parquet file is empty"

def test_checksum_line_present(download_outputs):
    checksum_path = download_outputs["checksum"]
    lines = checksum_path.read_text(encoding="utf-8").splitlines()
    # Look for a line that ends with the parquet filename
    matches = [ln for ln in lines if "vaers_2020_2023.parquet" in ln]
    assert matches, "Checksum entry for the parquet file not found"

def test_summary_contents(download_outputs):
    summary_path = download_outputs["summary"]
    text = summary_path.read_text(encoding="utf-8")
    assert "VAERS 2020‑2023 dataset acquisition summary" in text
    assert "sha256:" in text
    assert "size_bytes:" in text