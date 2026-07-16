"""
Unit tests for the Edge Case Handler (T007).
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import os
import sys
import json
import tempfile

# Import the module under test
from src.utils.edge_case_handler import (
    detect_empty_or_short_texts,
    detect_missing_ratings,
    handle_edge_cases,
    log_exclusions,
    get_exclusion_summary,
    MIN_WORD_COUNT
)


@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame with varying text lengths and ratings."""
    return pd.DataFrame({
        "conversation_id": ["1", "2", "3", "4", "5"],
        "text_content": [
            "This is a long enough sentence for testing.",
            "Short.",
            "",
            "Another valid sentence with enough words here.",
            "Just two words"
        ],
        "authenticity_score": [4.0, 3.0, np.nan, 5.0, 2.0]
    })


@pytest.fixture
def temp_log_dir(tmp_path):
    """Create a temporary directory for log files."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir


def test_detect_empty_or_short_texts(sample_dataframe):
    """Test detection of empty and short texts."""
    valid_df, exclusions = detect_empty_or_short_texts(sample_dataframe, text_column="text_content")

    # Expected valid rows: indices 0 and 3 (length > 5 words)
    assert len(valid_df) == 2
    assert list(valid_df["conversation_id"]) == ["1", "4"]

    # Expected exclusions: indices 1, 2, 4
    assert len(exclusions) == 3
    reasons = [e["reason"] for e in exclusions]
    assert all(r == "short_or_empty_text" for r in reasons)


def test_detect_missing_ratings(sample_dataframe):
    """Test detection of missing ratings."""
    # Case 1: Missing ratings in the same dataframe
    valid_df, exclusions = detect_missing_ratings(
        sample_dataframe,
        ratings_df=None,
        text_id_column="conversation_id",
        rating_value_column="authenticity_score"
    )

    # Row 2 has NaN rating
    assert len(valid_df) == 4
    assert len(exclusions) == 1
    assert exclusions[0]["reason"] == "missing_rating"
    assert exclusions[0]["conversation_id"] == "3"


def test_handle_edge_cases(sample_dataframe, temp_log_dir):
    """Test the main orchestration function."""
    # This should pass because ratings exist (even if one is NaN, the check is for existence in separate df or column presence)
    # Wait, detect_missing_ratings checks for NaN in the column if ratings_df is None.
    # So row 2 (NaN) should be excluded.
    
    # Re-run detect_missing_ratings logic to confirm behavior
    # If ratings_df is None, it checks df[rating_value_column].isna()
    # So row 2 is excluded.
    
    result_df = handle_edge_cases(
        sample_dataframe,
        ratings_df=None,
        log_dir=temp_log_dir,
        min_words=5
    )

    # Should exclude short texts (indices 1, 2, 4) AND missing ratings (index 2)
    # But index 2 is already excluded by text length.
    # Index 4 is short (2 words).
    # Index 1 is short (1 word).
    # So only 0 and 3 should remain.
    assert len(result_df) == 2


def test_handle_edge_cases_with_logging(sample_dataframe, temp_log_dir):
    """Test that exclusions are logged correctly."""
    handle_edge_cases(
        sample_dataframe,
        ratings_df=None,
        log_dir=temp_log_dir,
        min_words=5
    )

    # Check if log files were created
    log_files = list(temp_log_dir.glob("*.json"))
    assert len(log_files) == 1
    
    with open(log_files[0], "r") as f:
        logs = json.load(f)
    
    assert len(logs) >= 3  # At least the short text exclusions


def test_get_exclusion_summary_no_log():
    """Test summary generation."""
    exclusions = [
        {"reason": "short_or_empty_text"},
        {"reason": "short_or_empty_text"},
        {"reason": "missing_rating"}
    ]
    summary = get_exclusion_summary(exclusions)
    assert summary["short_or_empty_text"] == 2
    assert summary["missing_rating"] == 1


def test_empty_dataframe():
    """Test handling of empty DataFrame."""
    empty_df = pd.DataFrame(columns=["conversation_id", "text_content", "authenticity_score"])
    valid_df, exclusions = detect_empty_or_short_texts(empty_df)
    assert len(valid_df) == 0
    assert len(exclusions) == 0


def test_handle_edge_cases_no_missing_ratings():
    """Test that pipeline does not halt when ratings are present."""
    df = pd.DataFrame({
        "conversation_id": ["1", "2"],
        "text_content": ["Valid text here.", "Another valid text."],
        "authenticity_score": [4.0, 5.0]
    })
    
    # Should not raise SystemExit
    result = handle_edge_cases(df, ratings_df=None)
    assert len(result) == 2


def test_dataframe_with_no_text_column():
    """Test handling when text column is missing."""
    df = pd.DataFrame({
        "conversation_id": ["1"],
        "authenticity_score": [4.0]
    })
    # Should return df unchanged and empty exclusions
    valid_df, exclusions = detect_empty_or_short_texts(df, text_column="text_content")
    assert len(valid_df) == 1
    assert len(exclusions) == 0


def test_dataframe_with_no_rating_column():
    """Test handling when rating column is missing and no ratings_df provided."""
    df = pd.DataFrame({
        "conversation_id": ["1"],
        "text_content": ["Valid text."]
    })
    with pytest.raises(ValueError, match="Rating value column"):
        detect_missing_ratings(df, ratings_df=None)


def test_log_exclusions(temp_log_dir):
    """Test writing exclusion logs."""
    exclusions = [{"reason": "test", "id": 1}]
    log_file = log_exclusions(exclusions, temp_log_dir, prefix="test_log")
    assert log_file.exists()
    with open(log_file, "r") as f:
        data = json.load(f)
    assert data[0]["reason"] == "test"


def test_handle_edge_cases_with_separate_ratings():
    """Test handling with a separate ratings DataFrame."""
    text_df = pd.DataFrame({
        "conversation_id": ["1", "2", "3"],
        "text_content": ["Valid text.", "Valid text.", "Valid text."]
    })
    ratings_df = pd.DataFrame({
        "conversation_id": ["1", "2"],
        "authenticity_score": [4.0, 5.0]
    })
    
    # ID "3" is missing from ratings
    valid_df, exclusions = detect_missing_ratings(
        text_df,
        ratings_df=ratings_df,
        text_id_column="conversation_id",
        rating_id_column="conversation_id"
    )
    
    assert len(valid_df) == 2
    assert len(exclusions) == 1
    assert exclusions[0]["conversation_id"] == "3"


def test_short_text_detection_edge_cases():
    """Test edge cases for short text detection."""
    df = pd.DataFrame({
        "conversation_id": ["1", "2", "3", "4"],
        "text_content": [
            None,           # NaN
            "",             # Empty string
            "   ",          # Whitespace only
            "One word"      # Too short
        ]
    })
    valid_df, exclusions = detect_empty_or_short_texts(df)
    assert len(valid_df) == 0
    assert len(exclusions) == 4


def test_missing_ratings_detection_edge_cases():
    """Test edge cases for missing ratings detection."""
    df = pd.DataFrame({
        "conversation_id": ["1", "2"],
        "authenticity_score": [None, np.nan]
    })
    valid_df, exclusions = detect_missing_ratings(df, ratings_df=None)
    assert len(valid_df) == 0
    assert len(exclusions) == 2
