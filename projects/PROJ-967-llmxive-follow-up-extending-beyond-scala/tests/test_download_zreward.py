"""
Tests for the Z-Reward dataset downloader.
These tests verify the validation logic and error handling.
Note: These tests do NOT actually download the dataset to avoid network dependencies in CI.
Instead, they mock the download and test the validation logic.
"""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.download_zreward import validate_columns, REQUIRED_COLUMNS, RUBRIC_DIMENSIONS


def create_mock_dataframe():
    """Create a mock dataframe that matches the expected schema."""
    data = {
        "prompt": ["Sample 1", "Sample 2"],
        "image_url": ["url1", "url2"],
        "teacher_scores": [
            {"Alignment": 0.8, "Realism": 0.7, "Aesthetics": 0.9, "Plausibility": 0.6},
            {"Alignment": 0.5, "Realism": 0.6, "Aesthetics": 0.4, "Plausibility": 0.5}
        ],
        "student_scalar": [0.75, 0.55],
        "human_annotations": [
            {"Alignment": 0.85, "Realism": 0.75, "Aesthetics": 0.88, "Plausibility": 0.65},
            {"Alignment": 0.55, "Realism": 0.65, "Aesthetics": 0.45, "Plausibility": 0.55}
        ],
        "primary_dimension": ["Alignment", "Realism"]
    }
    return pd.DataFrame(data)


def test_validate_columns_valid():
    """Test validation with a valid dataframe."""
    df = create_mock_dataframe()
    is_valid, errors = validate_columns(df, MagicMock())
    assert is_valid is True
    assert len(errors) == 0


def test_validate_columns_missing_top_level():
    """Test validation with missing top-level columns."""
    df = create_mock_dataframe()
    df = df.drop(columns=["prompt"])
    is_valid, errors = validate_columns(df, MagicMock())
    assert is_valid is False
    assert "prompt" in errors


def test_validate_columns_invalid_teacher_scores():
    """Test validation with invalid teacher_scores structure."""
    df = create_mock_dataframe()
    df.loc[0, "teacher_scores"] = "not a dict"
    is_valid, errors = validate_columns(df, MagicMock())
    assert is_valid is False
    assert any("teacher_scores" in err for err in errors)


def test_validate_columns_missing_rubric_dimensions():
    """Test validation with missing rubric dimensions in teacher_scores."""
    df = create_mock_dataframe()
    # Remove one dimension
    df.loc[0, "teacher_scores"] = {"Alignment": 0.8, "Realism": 0.7, "Aesthetics": 0.9}
    is_valid, errors = validate_columns(df, MagicMock())
    assert is_valid is False
    assert any("missing rubric dimensions" in err for err in errors)


def test_validate_columns_nan_primary_dimension():
    """Test validation with NaN in primary_dimension."""
    df = create_mock_dataframe()
    df.loc[0, "primary_dimension"] = None
    is_valid, errors = validate_columns(df, MagicMock())
    assert is_valid is False
    assert any("primary_dimension contains NaN" in err for err in errors)
