"""
Unit tests for T025b: load_and_validate_data function.
"""
import pytest
import pandas as pd
import os
import tempfile
from pathlib import Path

# Import the function to test
# Note: Adjust import path based on execution context
try:
    from code.analysis.run_analysis import load_and_validate_data
except ImportError:
    # Fallback for direct execution context
    from analysis.run_analysis import load_and_validate_data

def create_temp_csv(data: dict, filename: str = "test_data.csv"):
    """Helper to create a temporary CSV file with given data."""
    fd, path = tempfile.mkstemp(suffix=".csv")
    with os.fdopen(fd, 'w') as f:
        df = pd.DataFrame(data)
        df.to_csv(f, index=False)
    return path

def test_load_valid_data():
    """Test loading a valid CSV file."""
    data = {
        'participant_id': ['P001', 'P002'],
        'interface_type': ['traditional', 'explainable'],
        'completion_time_seconds': [45.0, 40.0],
        'error_count': [2, 1],
        'sus_score': [75, 80],
        'explanation_engagement_time_seconds': [0.0, 10.0]
    }
    path = create_temp_csv(data)
    try:
        df = load_and_validate_data(path)
        assert df is not None
        assert len(df) == 2
        assert df['interface_type'].iloc[1] == 'explainable'
    finally:
        os.remove(path)

def test_missing_columns():
    """Test that missing columns raise an error."""
    data = {
        'participant_id': ['P001'],
        'interface_type': ['traditional'],
        # Missing completion_time_seconds
    }
    path = create_temp_csv(data)
    try:
        with pytest.raises(ValueError):
            load_and_validate_data(path)
    finally:
        os.remove(path)

def test_invalid_interface_type():
    """Test that invalid interface types raise an error."""
    data = {
        'participant_id': ['P001'],
        'interface_type': ['invalid_type'],
        'completion_time_seconds': [45.0],
        'error_count': [2],
        'sus_score': [75],
        'explanation_engagement_time_seconds': [0.0]
    }
    path = create_temp_csv(data)
    try:
        with pytest.raises(ValueError):
            load_and_validate_data(path)
    finally:
        os.remove(path)

def test_negative_completion_time():
    """Test that negative completion time raises an error."""
    data = {
        'participant_id': ['P001'],
        'interface_type': ['traditional'],
        'completion_time_seconds': [-5.0],
        'error_count': [2],
        'sus_score': [75],
        'explanation_engagement_time_seconds': [0.0]
    }
    path = create_temp_csv(data)
    try:
        with pytest.raises(ValueError):
            load_and_validate_data(path)
    finally:
        os.remove(path)

def test_sus_score_out_of_range():
    """Test that SUS score out of range raises an error."""
    data = {
        'participant_id': ['P001'],
        'interface_type': ['traditional'],
        'completion_time_seconds': [45.0],
        'error_count': [2],
        'sus_score': [150], # Out of range
        'explanation_engagement_time_seconds': [0.0]
    }
    path = create_temp_csv(data)
    try:
        with pytest.raises(ValueError):
            load_and_validate_data(path)
    finally:
        os.remove(path)

def test_file_not_found():
    """Test that missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_and_validate_data("non_existent_file.csv")