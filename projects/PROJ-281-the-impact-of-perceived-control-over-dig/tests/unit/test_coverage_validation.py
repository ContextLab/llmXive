"""
Unit tests for coverage validation logic.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

# Mock config to use temp directories
from code.config import CONFIG

from code.services.coverage_validation import validate_coverage


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory structure mimicking data/processed/."""
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    return processed_dir


@pytest.fixture
def mock_config(temp_data_dir):
    """Patch CONFIG to point to temporary directories."""
    with patch.object(CONFIG, 'DATA_PROCESSED_DIR', temp_data_dir):
        with patch.object(CONFIG, 'RUN_TIMESTAMP', pd.Timestamp.now()):
            yield CONFIG


def test_coverage_success(mock_config, temp_data_dir):
    """Test that validation passes when coverage is >= 95%."""
    # Create preprocessed file with 100 rows
    df_pre = pd.DataFrame({"text": [f"row_{i}" for i in range(100)]})
    pre_path = temp_data_dir / "preprocessed_text.csv"
    df_pre.to_csv(pre_path, index=False)

    # Create scoring file with 95 rows (95% coverage)
    df_score = pd.DataFrame({"text": [f"row_{i}" for i in range(95)], "anxiety_score": [0.5]*95, "confidence_score": [0.8]*95})
    score_path = temp_data_dir / "scoring_results.csv"
    df_score.to_csv(score_path, index=False)

    # Run validation
    report = validate_coverage()

    assert report["is_success"] is True
    assert report["coverage_percentage"] == 95.0
    assert report["preprocessed_count"] == 100
    assert report["scoring_count"] == 95

    # Verify file was written
    report_path = temp_data_dir / "coverage_report.json"
    assert report_path.exists()
    with open(report_path) as f:
        saved_report = json.load(f)
    assert saved_report["is_success"] is True


def test_coverage_failure(mock_config, temp_data_dir):
    """Test that validation fails when coverage is < 95%."""
    # Create preprocessed file with 100 rows
    df_pre = pd.DataFrame({"text": [f"row_{i}" for i in range(100)]})
    pre_path = temp_data_dir / "preprocessed_text.csv"
    df_pre.to_csv(pre_path, index=False)

    # Create scoring file with 94 rows (94% coverage)
    df_score = pd.DataFrame({"text": [f"row_{i}" for i in range(94)], "anxiety_score": [0.5]*94, "confidence_score": [0.8]*94})
    score_path = temp_data_dir / "scoring_results.csv"
    df_score.to_csv(score_path, index=False)

    # Run validation - should raise ValueError
    with pytest.raises(ValueError, match="Coverage validation failed"):
        validate_coverage()


def test_missing_preprocessed_file(mock_config, temp_data_dir):
    """Test that FileNotFoundError is raised if preprocessed file is missing."""
    # Create scoring file only
    df_score = pd.DataFrame({"text": ["row_0"], "anxiety_score": [0.5], "confidence_score": [0.8]})
    score_path = temp_data_dir / "scoring_results.csv"
    df_score.to_csv(score_path, index=False)

    with pytest.raises(FileNotFoundError, match="Preprocessed text file not found"):
        validate_coverage()


def test_missing_scoring_file(mock_config, temp_data_dir):
    """Test that FileNotFoundError is raised if scoring file is missing."""
    # Create preprocessed file only
    df_pre = pd.DataFrame({"text": ["row_0"]})
    pre_path = temp_data_dir / "preprocessed_text.csv"
    df_pre.to_csv(pre_path, index=False)

    with pytest.raises(FileNotFoundError, match="Scoring results file not found"):
        validate_coverage()


def test_empty_preprocessed_file(mock_config, temp_data_dir):
    """Test handling of empty preprocessed file."""
    # Create empty preprocessed file
    df_pre = pd.DataFrame(columns=["text"])
    pre_path = temp_data_dir / "preprocessed_text.csv"
    df_pre.to_csv(pre_path, index=False)

    # Create empty scoring file
    df_score = pd.DataFrame(columns=["text", "anxiety_score", "confidence_score"])
    score_path = temp_data_dir / "scoring_results.csv"
    df_score.to_csv(score_path, index=False)

    with pytest.raises(ValueError, match="Coverage validation failed"):
        validate_coverage()