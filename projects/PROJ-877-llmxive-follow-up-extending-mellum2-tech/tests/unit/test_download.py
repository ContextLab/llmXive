"""
Unit tests for the dataset download and sampling script (code/data/download.py).

The tests verify that:
* The script runs without raising an exception (network errors will cause the test to be skipped).
* The resulting Parquet file exists.
* The Parquet file contains exactly ``sample_size`` rows for each target language.
* The checksum file is created and contains a valid SHA‑256 hash.
"""

import hashlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

from llmxive_toolkit import paths

# Import the module under test to reuse its argument parser defaults.
from code.data import download

@pytest.mark.timeout(300)
def test_download_and_sampling(tmp_path, monkeypatch):
    """
    Execute the download script with a small sample size and verify output artifacts.
    """
    # Use a very small sample size to keep the test fast.
    sample_size = 10

    # Patch the config values used by the script to ensure determinism.
    monkeypatch.setattr(
        "code.config.SEED", 42, raising=False
    )
    monkeypatch.setattr(
        "code.config.SAMPLE_SIZE_PER_LANGUAGE", sample_size, raising=False
    )

    # Run the script's main function directly (no CLI needed).
    exit_code = download.main(
        ["--sample-size", str(sample_size), "--seed", "42"]
    )
    assert exit_code == 0

    # Verify Parquet output.
    parquet_path = paths.data("processed", "raw_chunks.parquet")
    assert parquet_path.is_file()

    # Load with pandas to inspect row counts.
    import pandas as pd

    df = pd.read_parquet(parquet_path)
    assert set(df["language"].unique()) == {"Python", "Java"}
    for lang in ["Python", "Java"]:
        assert (
            df[df["language"] == lang].shape[0] == sample_size
        ), f"Incorrect row count for {lang}"

    # Verify checksum file.
    checksum_path = paths.data("checksums.txt")
    assert checksum_path.is_file()
    line = checksum_path.read_text().strip()
    checksum, filename = line.split()
    assert filename == parquet_path.name

    # Re‑compute checksum to ensure correctness.
    sha256 = hashlib.sha256()
    with parquet_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    assert sha256.hexdigest() == checksum