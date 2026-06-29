"""
Unit test for the validation subset selection script (T064).

The test creates minimal synthetic agency scores and external scale files,
runs the selection script via its ``main`` function, and checks that:

  * The output CSV is created.
  * It contains at least 30 rows (or all rows if fewer are available).
  * The rows are a subset of the merged input data.
"""

import csv
import os
import sys
from pathlib import Path

import pandas as pd
import pytest

# Ensure the project root is on the import path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))

from code.validation.select_subset import (
    AGENCY_SCORES_PATH,
    EXTERNAL_DATA_DIR,
    VALIDATION_SUBSET_PATH,
    main,
)


@pytest.fixture
def synthetic_data(tmp_path: Path):
    # Create synthetic agency scores
    agency_path = AGENCY_SCORES_PATH
    agency_path.parent.mkdir(parents=True, exist_ok=True)
    agency_df = pd.DataFrame(
        {
            "session_id": [f"s{i}" for i in range(1, 101)],
            "agency_score": [i / 100 for i in range(1, 101)],
        }
    )
    agency_df.to_csv(agency_path, index=False)

    # Create synthetic external scale file
    external_dir = EXTERNAL_DATA_DIR
    external_dir.mkdir(parents=True, exist_ok=True)
    external_path = external_dir / "external_scale.csv"
    external_df = pd.DataFrame(
        {
            "session_id": [f"s{i}" for i in range(1, 101)],
            "external_score": [i % 7 for i in range(1, 101)],
        }
    )
    external_df.to_csv(external_path, index=False)

    yield

    # Cleanup
    if agency_path.is_file():
        agency_path.unlink()
    if external_path.is_file():
        external_path.unlink()
    if VALIDATION_SUBSET_PATH.is_file():
        VALIDATION_SUBSET_PATH.unlink()


def test_validation_subset_creation(synthetic_data):
    # Run the script
    main([])

    # Verify output exists
    assert VALIDATION_SUBSET_PATH.is_file(), "Subset CSV was not created."

    # Load and validate contents
    subset_df = pd.read_csv(VALIDATION_SUBSET_PATH)

    # Should have at least 30 rows (or the total number of available rows)
    expected_min = min(30, 100)  # we generated 100 rows total
    assert len(subset_df) >= expected_min

    # All rows must have session_ids present in the original agency scores
    original_ids = set(pd.read_csv(AGENCY_SCORES_PATH)["session_id"])
    assert set(subset_df["session_id"]).issubset(original_ids)

    # Ensure the required columns are present
    assert {"session_id", "agency_score", "external_score"} <= set(subset_df.columns)