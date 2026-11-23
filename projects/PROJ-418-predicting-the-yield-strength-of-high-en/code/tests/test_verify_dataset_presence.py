"""
Unit tests for the ``verify_dataset_presence`` utility (Task T016).
The tests create a temporary project‑root structure, place a CSV file at
``data/raw/heas_raw.csv`` and check that the verification logic behaves
correctly in three scenarios:
  1. File missing → FileNotFoundError.
  2. Insufficient rows → ValueError.
  3. Sufficient rows → no exception (exit code 0).
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

import pandas as pd
import pytest

# Ensure the project root (the temporary directory) is on sys.path so that
# imports resolve to the freshly‑created package layout.
@pytest.fixture
def temp_project_root():
    original_cwd = os.getcwd()
    temp_dir = tempfile.mkdtemp()
    os.chdir(temp_dir)
    # The code under test uses ``llmxive_toolkit.paths`` which creates
    # directories relative to the current working directory, so we need a
    # clean cwd.
    yield Path(temp_dir)
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_missing_file_raises(temp_project_root):
    """When the raw CSV does not exist, a FileNotFoundError should be raised."""
    from code.data.verify_dataset_presence import verify_dataset_presence

    # Ensure the file truly does not exist
    raw_path = temp_project_root / "data" / "raw" / "heas_raw.csv"
    if raw_path.is_file():
        raw_path.unlink()

    with pytest.raises(FileNotFoundError):
        verify_dataset_presence(min_records=10)


def test_insufficient_rows_raises(temp_project_root):
    """If the CSV exists but has fewer rows than required, raise ValueError."""
    from code.data.verify_dataset_presence import verify_dataset_presence

    raw_dir = temp_project_root / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / "heas_raw.csv"

    # Create a CSV with only 3 rows (plus header)
    df = pd.DataFrame(
        {
            "composition": ["A", "B", "C"],
            "yield_strength": [100, 200, 150],
        }
    )
    df.to_csv(raw_path, index=False)

    with pytest.raises(ValueError) as excinfo:
        verify_dataset_presence(min_records=5)
    assert "contains only 3 records" in str(excinfo.value)


def test_sufficient_rows_passes(temp_project_root):
    """When the CSV meets the record count requirement, verification succeeds."""
    from code.data.verify_dataset_presence import verify_dataset_presence

    raw_dir = temp_project_root / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / "heas_raw.csv"

    # Create a CSV with 10 rows
    df = pd.DataFrame(
        {
            "composition": [f"Alloy{i}" for i in range(10)],
            "yield_strength": [i * 10 for i in range(10)],
        }
    )
    df.to_csv(raw_path, index=False)

    # Should not raise any exception
    verify_dataset_presence(min_records=5)  # explicit min_records for clarity