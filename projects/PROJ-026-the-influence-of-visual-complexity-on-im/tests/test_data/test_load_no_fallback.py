"""
Test for T059: Enforce Real Data Integrity in Production.

Verifies that the data loader raises RuntimeError when real data is missing
in production mode (no --null-effect flag, not in CI).
"""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd

# Import the module to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.load import load_response_logs
from config import get_project_root

@pytest.fixture
def mock_missing_real_data(tmp_path):
    """Fixture to simulate missing real data."""
    # Create a temporary project root
    project_root = tmp_path
    
    # Ensure the real data path does NOT exist
    real_data_dir = project_root / "data" / "raw" / "responses"
    real_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Do NOT create participants.csv
    
    with patch('data.load.get_project_root', return_value=project_root):
        yield project_root

@pytest.fixture
def mock_github_actions_true():
    """Fixture to simulate CI environment."""
    with patch.dict(os.environ, {'GITHUB_ACTIONS': 'true'}):
        yield

@pytest.fixture
def mock_github_actions_false():
    """Fixture to simulate local environment."""
    # Ensure GITHUB_ACTIONS is not set or is 'false'
    env = os.environ.copy()
    env.pop('GITHUB_ACTIONS', None)
    with patch.dict(os.environ, env, clear=False):
        yield

def test_load_raises_runtime_error_missing_data_local_mode(mock_missing_real_data, mock_github_actions_false):
    """
    Test that load_response_logs raises RuntimeError when:
    1. Real data is missing
    2. Not in CI mode (GITHUB_ACTIONS not set)
    3. --null-effect flag is NOT set
    """
    with pytest.raises(RuntimeError) as exc_info:
        load_response_logs(force_synthetic=False)
    
    assert "Real data file not found" in str(exc_info.value)
    assert "production mode" in str(exc_info.value).lower()
    assert "strictly required" in str(exc_info.value).lower()

def test_load_succeeds_with_null_effect_flag(mock_missing_real_data, mock_github_actions_false, tmp_path):
    """
    Test that load_response_logs succeeds when --null-effect flag is set,
    even if real data is missing.
    """
    # This should NOT raise an error because force_synthetic=True
    df = load_response_logs(force_synthetic=True, output_path="data/raw/responses/synthetic_participants.csv")
    
    assert df is not None
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert 'participant_id' in df.columns

def test_load_succeeds_in_ci_mode(mock_missing_real_data, mock_github_actions_true):
    """
    Test that load_response_logs succeeds when GITHUB_ACTIONS is set,
    even if real data is missing.
    """
    # In CI mode, the function should generate synthetic data
    # We need to mock the environment variable check
    with patch('os.environ.get', return_value='true'):
        df = load_response_logs(force_synthetic=False)
    
    assert df is not None
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0

def test_load_with_real_data(tmp_path):
    """
    Test that load_response_logs succeeds when real data exists.
    """
    project_root = tmp_path
    real_data_dir = project_root / "data" / "raw" / "responses"
    real_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a valid real data file
    real_data_path = real_data_dir / "participants.csv"
    synthetic_df = pd.DataFrame({
        'participant_id': ['sub-001', 'sub-002'],
        'session_id': ['ses-01', 'ses-01'],
        'trial_idx': [0, 0],
        'complexity_condition': ['Low', 'Low'],
        'reaction_time_ms': [600, 650],
        'is_correct': [True, True],
        'timestamp': ['2023-01-01', '2023-01-01']
    })
    synthetic_df.to_csv(real_data_path, index=False)
    
    with patch('data.load.get_project_root', return_value=project_root):
        with patch('os.environ.get', return_value=None):  # Not CI
            df = load_response_logs(force_synthetic=False)
    
    assert df is not None
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df.columns) == list(synthetic_df.columns)

def test_load_checksum_verification_failure(tmp_path):
    """
    Test that load_response_logs raises ValueError if checksum mismatch.
    """
    project_root = tmp_path
    real_data_dir = project_root / "data" / "raw" / "responses"
    real_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create real data file
    real_data_path = real_data_dir / "participants.csv"
    synthetic_df = pd.DataFrame({
        'participant_id': ['sub-001'],
        'session_id': ['ses-01'],
        'trial_idx': [0],
        'complexity_condition': ['Low'],
        'reaction_time_ms': [600],
        'is_correct': [True],
        'timestamp': ['2023-01-01']
    })
    synthetic_df.to_csv(real_data_path, index=False)
    
    # Create checksums file with WRONG hash
    checksums_file = project_root / "data" / "checksums.json"
    import json
    wrong_hash = "0" * 64  # Invalid hash
    checksums = {str(real_data_path.relative_to(project_root)): wrong_hash}
    with open(checksums_file, 'w') as f:
        json.dump(checksums, f)
    
    with patch('data.load.get_project_root', return_value=project_root):
        with patch('os.environ.get', return_value=None):
            with pytest.raises(ValueError) as exc_info:
                load_response_logs(force_synthetic=False)
    
    assert "Checksum mismatch" in str(exc_info.value)
