"""
Unit tests for the ``code/data/download.py`` module (Task T002).
The tests verify that:
1. The reservoir sampling returns the expected number of records.
2. The language distribution matches the requested split.
3. The Parquet writer creates a file with the correct schema.
"""
import os
import json
from pathlib import Path

import pytest

# Import the functions directly (avoid invoking the CLI)
from code.data.download import fetch_and_sample, write_parquet_and_checksum


@pytest.fixture(scope="module")
def small_sample():
    """Fetch a tiny sample (2 per language) to keep test runtime low."""
    records = fetch_and_sample(
        languages=["python", "java"],
        total_sample_size=4,
        seed=42
    )
    return records


def test_sample_size_and_balance(small_sample):
    """Ensure we get exactly 4 records, 2 per language."""
    assert len(small_sample) == 4, "Unexpected total sample size"
    langs = [rec["language"] for rec in small_sample]
    assert langs.count("python") == 2, "Python balance incorrect"
    assert langs.count("java") == 2, "Java balance incorrect"


def test_parquet_output(tmp_path: Path, small_sample):
    """Write the sampled records to Parquet and verify schema & checksum."""
    parquet_file = tmp_path / "raw_chunks.parquet"
    checksum_file = tmp_path / "checksums.txt"

    write_parquet_and_checksum(
        records=small_sample,
        output_parquet=parquet_file,
        checksum_path=checksum_file
    )

    # Verify Parquet file exists and is non‑empty
    assert parquet_file.is_file()
    assert parquet_file.stat().st_size > 0

    # Verify checksum file exists and contains a SHA‑256 hash
    assert checksum_file.is_file()
    content = checksum_file.read_text().strip()
    parts = content.split()
    assert len(parts) == 2, "Checksum file format incorrect"
    sha, filename = parts
    assert len(sha) == 64, "Checksum length mismatch"
    assert filename == parquet_file.name, "Checksum filename mismatch"

    # Verify Parquet column names
    import pandas as pd

    df = pd.read_parquet(parquet_file, engine="pyarrow")
    expected_cols = ["id", "repo_name", "language", "content", "status"]
    assert list(df.columns) == expected_cols, "Parquet schema mismatch"
    assert len(df) == 4, "Parquet row count mismatch"


def test_invalid_language_handling():
    """Request a language not present – should return an empty list."""
    records = fetch_and_sample(
        languages=["nonexistentlang"],
        total_sample_size=2,
        seed=123
    )
    assert records == [], "Expected no records for an unsupported language"


# The tests are deliberately lightweight to respect the CI runtime limits.