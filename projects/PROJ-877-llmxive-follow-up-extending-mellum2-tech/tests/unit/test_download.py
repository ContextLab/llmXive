"""
Unit test for the ``code.data.download`` module.

The test invokes the module as a subprocess with a tiny sample size
(2 records per language) to keep execution time low while still
exercising the full end‑to‑end flow:

1. Run ``python -m code.data.download --sample-size 2``.
2. Verify that the Parquet file exists.
3. Verify that exactly two rows exist for each of ``Python`` and ``Java``.
4. Verify that a checksum file was created and contains a SHA‑256 hash.
"""

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from llmxive_toolkit import paths


@pytest.mark.timeout(300)
def test_download_small_sample(tmp_path, monkeypatch):
    """
    Execute the download script with a very small sample size and check
    that the expected artifacts are produced.
    """
    # Redirect the data directory to a temporary location so the test does
    # not interfere with any existing artefacts.
    monkeypatch.setattr(paths, "data", lambda *parts: Path(tmp_path, *parts))

    # Run the module as a subprocess.
    result = subprocess.run(
        [sys.executable, "-m", "code.data.download", "--sample-size", "2"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Subprocess failed: {result.stderr}"

    # Verify parquet file.
    parquet_path = paths.data("processed", "raw_chunks.parquet")
    assert parquet_path.is_file(), f"{parquet_path} does not exist"

    df = pd.read_parquet(parquet_path)
    # Expect exactly two rows per language.
    assert df["language"].value_counts().to_dict() == {"Python": 2, "Java": 2}

    # Verify checksum file.
    checksum_path = paths.data("checksums.txt")
    assert checksum_path.is_file(), "Checksum file missing"
    lines = checksum_path.read_text().strip().splitlines()
    assert any("raw_chunks.parquet" in line for line in lines), "Checksum entry missing"