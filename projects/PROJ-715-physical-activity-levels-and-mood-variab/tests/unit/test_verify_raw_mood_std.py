"""
Unit tests for the raw mood_std verification logic (Task T019b).
"""
import pytest
import pandas as pd
import numpy as np
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.verify_raw_mood_std import verify_raw_mood_std

@pytest.fixture
def mock_csv_file(tmp_path):
    """Create a temporary CSV file with valid raw mood_std data."""
    data = {
        'participant_id': ['P1', 'P1', 'P2', 'P2'],
        'date': ['2023-01-01', '2023-01-02', '2023-01-01', '2023-01-02'],
        'total_steps': [5000, 6000, 4000, 7000],
        'mean_mood': [3.5, 4.0, 2.5, 3.0],
        'mood_std': [0.5, 0.0, 1.2, 0.8],  # Raw std, non-negative
        'n_mood_ratings': [5, 3, 4, 6]
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / "daily_aggregates.csv"
    df.to_csv(csv_path, index=False)
    return str(csv_path)

@pytest.fixture
def mock_csv_file_nan(tmp_path):
    """Create a temporary CSV file with NaN in mood_std."""
    data = {
        'participant_id': ['P1', 'P1'],
        'date': ['2023-01-01', '2023-01-02'],
        'total_steps': [5000, 6000],
        'mean_mood': [3.5, 4.0],
        'mood_std': [0.5, np.nan],  # Contains NaN
        'n_mood_ratings': [5, 3]
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / "daily_aggregates.csv"
    df.to_csv(csv_path, index=False)
    return str(csv_path)

@pytest.fixture
def mock_csv_file_negative(tmp_path):
    """Create a temporary CSV file with negative mood_std."""
    data = {
        'participant_id': ['P1', 'P1'],
        'date': ['2023-01-01', '2023-01-02'],
        'total_steps': [5000, 6000],
        'mean_mood': [3.5, 4.0],
        'mood_std': [0.5, -0.2],  # Contains negative
        'n_mood_ratings': [5, 3]
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / "daily_aggregates.csv"
    df.to_csv(csv_path, index=False)
    return str(csv_path)

def test_verify_valid_raw_mood_std(mock_csv_file):
    """Test that valid raw mood_std passes verification."""
    with patch('code.verify_raw_mood_std.get_path', return_value=mock_csv_file):
        results = verify_raw_mood_std()
    
    assert results["verification_status"] == "PASSED"
    assert results["checks"]["no_nan"] is True
    assert results["checks"]["no_inf"] is True
    assert results["checks"]["no_negative_values"] is True
    assert results["checks"]["looks_like_raw_std"] is True

def test_verify_nan_in_mood_std(mock_csv_file_nan):
    """Test that NaN in mood_std causes verification to fail."""
    with patch('code.verify_raw_mood_std.get_path', return_value=mock_csv_file_nan):
        results = verify_raw_mood_std()
    
    assert results["verification_status"] == "FAILED"
    assert results["checks"]["no_nan"] is False

def test_verify_negative_mood_std(mock_csv_file_negative):
    """Test that negative mood_std causes verification to fail."""
    with patch('code.verify_raw_mood_std.get_path', return_value=mock_csv_file_negative):
        results = verify_raw_mood_std()
    
    assert results["verification_status"] == "FAILED"
    assert results["checks"]["no_negative_values"] is False

def test_verify_missing_column(tmp_path):
    """Test that missing mood_std column causes verification to fail."""
    data = {
        'participant_id': ['P1'],
        'date': ['2023-01-01'],
        'total_steps': [5000],
        'mean_mood': [3.5],
        # mood_std missing
        'n_mood_ratings': [5]
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / "daily_aggregates.csv"
    df.to_csv(csv_path, index=False)

    with patch('code.verify_raw_mood_std.get_path', return_value=str(csv_path)):
        results = verify_raw_mood_std()
    
    assert results["verification_status"] == "FAILED"
    assert "Column 'mood_std' not found" in results.get("error", "")

def test_verify_zero_std_allowed(mock_csv_file):
    """Test that zero std (all ratings identical) is allowed."""
    # The mock_csv_file already has a 0.0 value in mood_std
    with patch('code.verify_raw_mood_std.get_path', return_value=mock_csv_file):
        results = verify_raw_mood_std()
    
    assert results["verification_status"] == "PASSED"
    # 0.0 is non-negative, so it should pass
    assert results["checks"]["no_negative_values"] is True