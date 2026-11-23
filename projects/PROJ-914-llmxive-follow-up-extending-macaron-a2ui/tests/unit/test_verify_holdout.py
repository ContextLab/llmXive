"""
Unit tests for the hold-out set verification logic.
"""
import os
import sys
import tempfile
import pytest
import pandas as pd
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data.verify_holdout import (
    verify_file_exists,
    verify_row_count,
    verify_columns,
    verify_no_missing_values,
    verify_labels,
    verify_complexity_score
)

@pytest.fixture
def valid_holdout_df():
    """Create a valid N=50 hold-out dataframe."""
    data = {
        'query': [f"Query {i}" for i in range(50)],
        'ground_truth_intent': ['High-Confidence' if i % 2 == 0 else 'Ambiguous' for i in range(50)],
        'complexity_score': [3.0 + (i % 5) for i in range(50)]
    }
    return pd.DataFrame(data)

@pytest.fixture
def invalid_row_count_df():
    """Create a dataframe with wrong row count."""
    data = {
        'query': [f"Query {i}" for i in range(49)],
        'ground_truth_intent': ['High-Confidence' for _ in range(49)],
        'complexity_score': [3.0 for _ in range(49)]
    }
    return pd.DataFrame(data)

@pytest.fixture
def missing_column_df():
    """Create a dataframe missing a required column."""
    data = {
        'query': [f"Query {i}" for i in range(50)],
        'ground_truth_intent': ['High-Confidence' for _ in range(50)],
        # Missing complexity_score
    }
    return pd.DataFrame(data)

@pytest.fixture
def missing_values_df():
    """Create a dataframe with missing values."""
    data = {
        'query': [f"Query {i}" if i != 5 else None for i in range(50)],
        'ground_truth_intent': ['High-Confidence' for _ in range(50)],
        'complexity_score': [3.0 for _ in range(50)]
    }
    return pd.DataFrame(data)

@pytest.fixture
def invalid_label_df():
    """Create a dataframe with invalid labels."""
    data = {
        'query': [f"Query {i}" for i in range(50)],
        'ground_truth_intent': ['High-Confidence' if i % 2 == 0 else 'Invalid-Label' for i in range(50)],
        'complexity_score': [3.0 for _ in range(50)]
    }
    return pd.DataFrame(data)

def test_verify_file_exists_success(tmp_path):
    file_path = tmp_path / "test.csv"
    file_path.touch()
    assert verify_file_exists(file_path) is True

def test_verify_file_exists_failure(tmp_path):
    file_path = tmp_path / "nonexistent.csv"
    assert verify_file_exists(file_path) is False

def test_verify_row_count_success(valid_holdout_df):
    assert verify_row_count(valid_holdout_df) is True

def test_verify_row_count_failure(invalid_row_count_df):
    assert verify_row_count(invalid_row_count_df) is False

def test_verify_columns_success(valid_holdout_df):
    assert verify_columns(valid_holdout_df) is True

def test_verify_columns_failure(missing_column_df):
    assert verify_columns(missing_column_df) is False

def test_verify_no_missing_values_success(valid_holdout_df):
    assert verify_no_missing_values(valid_holdout_df) is True

def test_verify_no_missing_values_failure(missing_values_df):
    assert verify_no_missing_values(missing_values_df) is False

def test_verify_labels_success(valid_holdout_df):
    assert verify_labels(valid_holdout_df) is True

def test_verify_labels_failure(invalid_label_df):
    assert verify_labels(invalid_label_df) is False

def test_verify_complexity_score_success(valid_holdout_df):
    assert verify_complexity_score(valid_holdout_df) is True

def test_verify_complexity_score_non_numeric():
    df = pd.DataFrame({
        'query': ['q1'],
        'ground_truth_intent': ['High-Confidence'],
        'complexity_score': ['not_a_number']
    })
    assert verify_complexity_score(df) is False