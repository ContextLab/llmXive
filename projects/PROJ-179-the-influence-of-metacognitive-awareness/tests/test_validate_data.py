"""
Unit tests for ``code/data/validate_data.py``.
The tests cover three scenarios:
  1. No CSV files present → FAIL.
  2. CSV present but missing required columns → FAIL.
  3. CSV present with required columns → PASS.
"""

import json
import os
import shutil
import tempfile
from pathlib import Path

import pandas as pd
import pytest

# Import the script as a module
from importlib import import_module

validate_module = import_module("data.validate_data")


@pytest.fixture
def raw_dir(tmp_path: Path):
    """Create a temporary ``data/raw`` directory for each test."""
    raw_path = tmp_path / "data" / "raw"
    raw_path.mkdir(parents=True)
    # Patch the module's RAW_DATA_DIR to point at the temporary directory
    validate_module.RAW_DATA_DIR = raw_path
    # Ensure the report path points inside the temporary tree as well
    validate_module.REPORT_PATH = tmp_path / "data" / "validation_report.json"
    return raw_path


def read_report(report_path: Path) -> dict:
    return json.loads(report_path.read_text())


def test_no_csv_found(raw_dir: Path):
    """When no CSV is present the script should report FAIL."""
    exit_code = validate_module.main()
    assert exit_code == 1
    report = read_report(validate_module.REPORT_PATH)
    assert report["status"] == "FAIL"
    assert "confidence_rating" in report["missing_fields"]
    assert "source_label" in report["missing_fields"]


def test_missing_required_columns(raw_dir: Path):
    """CSV exists but required columns are missing → FAIL."""
    df = pd.DataFrame(
        {
            "participant_id": [1, 2],
            "response_time": [0.5, 0.6],
        }
    )
    csv_path = raw_dir / "test.csv"
    df.to_csv(csv_path, index=False)

    with pytest.raises(ValueError):
        # The script is expected to raise ValueError for missing fields
        validate_module.main()

    report = read_report(validate_module.REPORT_PATH)
    assert report["status"] == "FAIL"
    # Both required columns should be listed as missing
    assert set(report["missing_fields"]) == {"confidence_rating", "source_label"}


def test_all_required_fields_present(raw_dir: Path):
    """CSV with required columns → PASS."""
    df = pd.DataFrame(
        {
            "participant_id": [1, 2],
            "confidence_rating": [0.8, 0.3],
            "source_label": ["A", "B"],
        }
    )
    csv_path = raw_dir / "valid.csv"
    df.to_csv(csv_path, index=False)

    exit_code = validate_module.main()
    assert exit_code == 0
    report = read_report(validate_module.REPORT_PATH)
    assert report["status"] == "PASS"