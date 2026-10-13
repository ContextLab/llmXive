"""
Integration tests for the Devign download and filtering steps.

The tests verify that:
  1. The Devign CSV is downloaded to the expected location.
  2. A SHA‑256 checksum is recorded in ``data/checksums.json`` and matches the file.
  3. The filtered Python dataset is written and contains at least the required
     number of distinct OWASP vulnerability types.
"""
import json
from pathlib import Path

import pandas as pd
import pytest

from llmxive_toolkit import paths

# Import the helper functions directly from the modules under test
from code.download_devign import compute_sha256, CHECKSUMS_PATH, CSV_DEST
from code.filter_human_python import (
    CSV_OUTPUT,
    REQUIRED_DISTINCT_TYPES,
    VULN_LABEL_COL,
)

@pytest.mark.dependency()
def test_devign_csv_exists():
    """The raw Devign CSV must exist after the download script runs."""
    assert CSV_DEST.is_file(), f"Expected CSV at {CSV_DEST} but it does not exist."

def test_checksum_recorded_and_matches():
    """The checksum file must contain a matching entry for the CSV."""
    # Load the checksums JSON
    assert CHECKSUMS_PATH.is_file(), "checksums.json was not created."
    with open(CHECKSUMS_PATH, "r", encoding="utf-8") as f:
        checksums = json.load(f)

    recorded = checksums.get(str(CSV_DEST))
    assert recorded, f"No checksum entry for {CSV_DEST} in {CHECKSUMS_PATH}"
    actual = compute_sha256(CSV_DEST)
    assert recorded == actual, (
        f"Checksum mismatch: recorded {recorded}, actual {actual}"
    )

@pytest.mark.dependency(depends=["test_devign_csv_exists"])
def test_filtered_python_dataset():
    """The filtered CSV must exist and meet the distinct‑type requirement."""
    assert CSV_OUTPUT.is_file(), f"Filtered CSV not found at {CSV_OUTPUT}"
    df = pd.read_csv(CSV_OUTPUT, dtype=str)
    # Ensure we have at least one row
    assert not df.empty, "Filtered dataset is empty."

    # Verify distinct OWASP vulnerability types count
    distinct = df[VULN_LABEL_COL].dropna().unique()
    assert (
        len(distinct) >= REQUIRED_DISTINCT_TYPES
    ), (
        f"Filtered dataset contains only {len(distinct)} distinct vulnerability "
        f"types; required minimum is {REQUIRED_DISTINCT_TYPES}."
    )