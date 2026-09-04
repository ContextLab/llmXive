"""
Unit tests for coverage validation logic.
"""
import json
import os
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from code.services.coverage_validation import validate_coverage, run_coverage_validation
from code.config import CONFIG


@pytest.fixture
def temp_csv_files(tmp_path):
    """Create temporary CSV files for testing."""
    preprocessed_file = tmp_path / "preprocessed_text.csv"
    scoring_file = tmp_path / "scoring_results.csv"
    report_file = tmp_path / "coverage_report.json"

    # Create preprocessed data
    preprocessed_data = pd.DataFrame({
        "text": ["Good morning", "Hello world", "Test post", "Another test", "Fifth post"],
        "user_id": [1, 2, 3, 4, 5]
    })
    preprocessed_data.to_csv(preprocessed_file, index=False)

    # Create scoring data (4 out of 5 rows scored - 80% coverage)
    scoring_data = pd.DataFrame({
        "text": ["Good morning", "Hello world", "Test post", "Another test"],
        "anxiety_score": [0.1, 0.2, 0.3, 0.4],
        "confidence_score": [0.8, 0.9, 0.7, 0.85]
    })
    scoring_data.to_csv(scoring_file, index=False)

    return {
        "preprocessed": preprocessed_file,
        "scoring": scoring_file,
        "report": report_file,
        "tmp_path": tmp_path
    }


def test_validate_coverage_below_threshold(temp_csv_files):
    """Test validation when coverage is below 95%."""
    result = validate_coverage(
        temp_csv_files["preprocessed"],
        temp_csv_files["scoring"]
    )

    assert result["total_input_rows"] == 5
    assert result["scored_rows"] == 4
    assert result["coverage_percentage"] == 80.0
    assert result["threshold_met"] is False
    assert result["status"] == "FAIL"
    assert "threshold not met" in result["reason"].lower()


def test_validate_coverage_above_threshold(temp_csv_files):
    """Test validation when coverage is above 95%."""
    # Create 100 input rows
    preprocessed_data = pd.DataFrame({
        "text": [f"Post {i}" for i in range(100)],
        "user_id": list(range(100))
    })
    temp_csv_files["preprocessed"].write_text(
        preprocessed_data.to_csv(index=False), encoding="utf-8"
    )

    # Score 96 rows (96%)
    scoring_data = pd.DataFrame({
        "text": [f"Post {i}" for i in range(96)],
        "anxiety_score": [0.1] * 96,
        "confidence_score": [0.8] * 96
    })
    temp_csv_files["scoring"].write_text(
        scoring_data.to_csv(index=False), encoding="utf-8"
    )

    result = validate_coverage(
        temp_csv_files["preprocessed"],
        temp_csv_files["scoring"]
    )

    assert result["total_input_rows"] == 100
    assert result["scored_rows"] == 96
    assert result["coverage_percentage"] == 96.0
    assert result["threshold_met"] is True
    assert result["status"] == "PASS"


def test_validate_coverage_empty_input(temp_csv_files):
    """Test validation when input dataset is empty."""
    empty_df = pd.DataFrame(columns=["text", "user_id"])
    temp_csv_files["preprocessed"].write_text(
        empty_df.to_csv(index=False), encoding="utf-8"
    )

    result = validate_coverage(
        temp_csv_files["preprocessed"],
        temp_csv_files["scoring"]
    )

    assert result["total_input_rows"] == 0
    assert result["scored_rows"] == 4
    assert result["coverage_percentage"] == 0.0
    assert result["threshold_met"] is False
    assert "empty" in result["reason"].lower()


def test_validate_coverage_missing_file(tmp_path):
    """Test validation raises error when input file is missing."""
    non_existent = tmp_path / "does_not_exist.csv"
    scoring_file = tmp_path / "scoring_results.csv"

    scoring_data = pd.DataFrame({
        "text": ["Test"],
        "anxiety_score": [0.1],
        "confidence_score": [0.8]
    })
    scoring_data.to_csv(scoring_file, index=False)

    with pytest.raises(FileNotFoundError):
        validate_coverage(non_existent, scoring_file)


@patch("code.services.coverage_validation.CONFIG")
def test_run_coverage_validation(mock_config, temp_csv_files):
    """Test the full pipeline run function."""
    mock_config.DATA_PROCESSED_DIR = temp_csv_files["tmp_path"]

    result = run_coverage_validation()

    assert "total_input_rows" in result
    assert "scored_rows" in result
    assert "coverage_percentage" in result
    assert "threshold_met" in result
    assert "status" in result

    # Verify report file was created
    report_path = temp_csv_files["tmp_path"] / "coverage_report.json"
    assert report_path.exists()

    with open(report_path, "r") as f:
        saved_report = json.load(f)

    assert saved_report == result
