"""
Unit tests for code/analysis/validate_human_data.py
"""
import os
import sys
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from analysis.validate_human_data import (
    check_file_exists,
    load_and_validate_data,
    check_unique_participants,
    check_for_synthetic_content
)

@pytest.fixture
def temp_csv_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_check_file_exists(temp_csv_dir):
    """Test file existence check."""
    valid_file = temp_csv_dir / "valid.csv"
    valid_file.touch()
    assert check_file_exists(valid_file) is True

    missing_file = temp_csv_dir / "missing.csv"
    assert check_file_exists(missing_file) is False

def test_load_and_validate_data_success(temp_csv_dir):
    """Test successful loading and schema validation."""
    file_path = temp_csv_dir / "data.csv"
    data = {
        'participant_id': ['P1', 'P2'],
        'stimulus_id': ['S1', 'S2'],
        'true_label': ['happy', 'sad'],
        'response_label': ['happy', 'sad'],
        'timestamp': ['2023-01-01', '2023-01-02']
    }
    pd.DataFrame(data).to_csv(file_path, index=False)

    df = load_and_validate_data(file_path)
    assert df is not None
    assert len(df) == 2

def test_load_and_validate_data_missing_columns(temp_csv_dir):
    """Test failure when columns are missing."""
    file_path = temp_csv_dir / "bad_data.csv"
    data = {
        'participant_id': ['P1'],
        'stimulus_id': ['S1']
        # Missing other required columns
    }
    pd.DataFrame(data).to_csv(file_path, index=False)

    df = load_and_validate_data(file_path)
    assert df is None

def test_check_unique_participants_success():
    """Test participant count validation."""
    df = pd.DataFrame({
        'participant_id': ['P1', 'P2', 'P3', 'P4', 'P5'],
        'stimulus_id': ['S1'] * 5,
        'true_label': ['h'] * 5,
        'response_label': ['h'] * 5,
        'timestamp': ['t'] * 5
    })
    assert check_unique_participants(df, min_count=5) is True

def test_check_unique_participants_failure():
    """Test participant count validation failure."""
    df = pd.DataFrame({
        'participant_id': ['P1', 'P2', 'P3'],
        'stimulus_id': ['S1'] * 3,
        'true_label': ['h'] * 3,
        'response_label': ['h'] * 3,
        'timestamp': ['t'] * 3
    })
    assert check_unique_participants(df, min_count=5) is False

def test_check_for_synthetic_content_duplicates(temp_csv_dir):
    """Test detection of synthetic content via duplicates."""
    file_path = temp_csv_dir / "synthetic.csv"
    # Create a dataset where every row is a duplicate
    data = {
        'participant_id': ['P1'] * 10,
        'stimulus_id': ['S1'] * 10,
        'true_label': ['happy'] * 10,
        'response_label': ['happy'] * 10,
        'timestamp': ['2023-01-01'] * 10
    }
    pd.DataFrame(data).to_csv(file_path, index=False)

    df = pd.read_csv(file_path)
    # This should return False because all rows are identical (synthetic)
    assert check_for_synthetic_content(df, file_path) is False

def test_check_for_synthetic_content_keywords(temp_csv_dir):
    """Test detection of synthetic content via keywords."""
    file_path = temp_csv_dir / "synthetic.csv"
    data = {
        'participant_id': ['P1', 'synthetic_user'],
        'stimulus_id': ['S1', 'S2'],
        'true_label': ['happy', 'sad'],
        'response_label': ['happy', 'sad'],
        'timestamp': ['2023-01-01', '2023-01-02']
    }
    pd.DataFrame(data).to_csv(file_path, index=False)

    df = pd.read_csv(file_path)
    assert check_for_synthetic_content(df, file_path) is False

def test_check_for_synthetic_content_real_data(temp_csv_dir):
    """Test that real-looking data passes."""
    file_path = temp_csv_dir / "real.csv"
    data = {
        'participant_id': ['P1', 'P2', 'P3', 'P4', 'P5', 'P6'],
        'stimulus_id': ['S1', 'S2', 'S3', 'S4', 'S5', 'S6'],
        'true_label': ['happy', 'sad', 'angry', 'happy', 'sad', 'fear'],
        'response_label': ['happy', 'sad', 'angry', 'happy', 'sad', 'fear'],
        'timestamp': [f'2023-01-0{i+1}' for i in range(6)]
    }
    pd.DataFrame(data).to_csv(file_path, index=False)

    df = pd.read_csv(file_path)
    assert check_for_synthetic_content(df, file_path) is True