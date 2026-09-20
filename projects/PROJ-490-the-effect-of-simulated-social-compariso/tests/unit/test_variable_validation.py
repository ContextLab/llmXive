import os
import json
import pytest
from pathlib import Path
import pandas as pd
import shutil
from unittest.mock import patch, MagicMock

from data.validate_raw import validate_raw_data_variables, validate_raw_directory, REQUIRED_VARS
from data.config import Config, get_config, reset_config
from data.download import DataFetchError

@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project structure for testing."""
    root = tmp_path / "test_project"
    root.mkdir()
    
    code_dir = root / "code"
    data_dir = root / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    state_dir = root / "state"
    
    raw_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)
    state_dir.mkdir(parents=True)
    
    # Create a minimal config file if needed, or rely on env
    config_file = root / "config.yaml"
    config_file.write_text(f"""
    raw_dir: {str(raw_dir)}
    processed_dir: {str(processed_dir)}
    state_dir: {str(state_dir)}
    seed: 42
    """)
    
    return root, raw_dir, processed_dir

@pytest.fixture
def mock_config(temp_project_dir):
    """Setup a mock config for the test."""
    root, raw_dir, processed_dir = temp_project_dir
    # Reset any global config state
    reset_config()
    # We will pass paths explicitly or mock get_config if needed
    # For this test, we'll mock the config object directly in the function
    return root, raw_dir, processed_dir

def test_validate_raw_data_variables_all_present(temp_project_dir):
    """Test that validation passes when all required variables are present."""
    root, raw_dir, processed_dir = temp_project_dir
    
    # Create a CSV with all required variables
    data = {
        'participant_id': ['1', '2'],
        'avatar_condition': [0, 1],
        'pre_self_esteem': [10.0, 12.0],
        'post_self_esteem': [11.0, 13.0],
        'comparison_tendency': [5.0, 6.0]
    }
    df = pd.DataFrame(data)
    csv_path = raw_dir / "data.csv"
    df.to_csv(csv_path, index=False)
    
    is_valid, missing = validate_raw_data_variables(raw_dir)
    
    assert is_valid is True
    assert missing == []

def test_validate_raw_data_variables_missing_one(temp_project_dir):
    """Test that validation fails when one required variable is missing."""
    root, raw_dir, processed_dir = temp_project_dir
    
    # Create a CSV missing 'comparison_tendency'
    data = {
        'participant_id': ['1', '2'],
        'avatar_condition': [0, 1],
        'pre_self_esteem': [10.0, 12.0],
        'post_self_esteem': [11.0, 13.0],
        # missing comparison_tendency
    }
    df = pd.DataFrame(data)
    csv_path = raw_dir / "data.csv"
    df.to_csv(csv_path, index=False)
    
    is_valid, missing = validate_raw_data_variables(raw_dir)
    
    assert is_valid is False
    assert 'comparison_tendency' in missing
    assert len(missing) == 1

def test_validate_raw_data_variables_missing_all(temp_project_dir):
    """Test that validation fails when all required variables are missing."""
    root, raw_dir, processed_dir = temp_project_dir
    
    # Create a CSV with no required variables
    data = {
        'id': [1, 2],
        'name': ['a', 'b']
    }
    df = pd.DataFrame(data)
    csv_path = raw_dir / "data.csv"
    df.to_csv(csv_path, index=False)
    
    is_valid, missing = validate_raw_data_variables(raw_dir)
    
    assert is_valid is False
    assert set(missing) == REQUIRED_VARS

def test_validate_raw_directory_triggers_synthetic_on_missing(temp_project_dir, mock_config):
    """
    Test that validate_raw_directory triggers synthetic generation when variables are missing.
    This tests the T013a fallback logic.
    """
    root, raw_dir, processed_dir = temp_project_dir
    
    # Create a CSV missing variables
    data = {
        'id': [1, 2],
        'name': ['a', 'b']
    }
    df = pd.DataFrame(data)
    csv_path = raw_dir / "data.csv"
    df.to_csv(csv_path, index=False)
    
    # Mock the synthetic generator to create a valid file
    valid_data = {
        'participant_id': ['1'],
        'avatar_condition': [0],
        'pre_self_esteem': [10.0],
        'post_self_esteem': [11.0],
        'comparison_tendency': [5.0]
    }
    
    with patch('data.validate_raw.generate_synthetic_dataset') as mock_gen:
        # Mock the return value to be the path where the file will be
        mock_gen.return_value = str(raw_dir / "synthetic_data.csv")
        
        # We also need to ensure that after the mock returns, the file exists
        # so the re-validation passes.
        # The function generate_synthetic_dataset is expected to write the file.
        # We'll mock it to write the file and return the path.
        def side_effect(path):
            pd.DataFrame(valid_data).to_csv(path / "synthetic_data.csv", index=False)
            return path / "synthetic_data.csv"
        
        mock_gen.side_effect = side_effect
        
        with patch('data.validate_raw.write_state_decision'):
            with patch('data.validate_raw.log_fallback_decision'):
                result = validate_raw_directory(raw_dir)
    
    assert result["status"] == "pass"
    assert result["missing_vars"] == []
    
    # Check that the output file was created
    output_file = processed_dir / "pre_imputation_validation.json"
    assert output_file.exists()
    
    with open(output_file) as f:
        saved_result = json.load(f)
    
    assert saved_result["status"] == "pass"

def test_validate_raw_directory_fails_if_synthetic_fails(temp_project_dir):
    """
    Test that validation fails if synthetic generation also fails.
    """
    root, raw_dir, processed_dir = temp_project_dir
    
    # Create a CSV missing variables
    data = {'id': [1]}
    df = pd.DataFrame(data)
    csv_path = raw_dir / "data.csv"
    df.to_csv(csv_path, index=False)
    
    with patch('data.validate_raw.generate_synthetic_dataset') as mock_gen:
        mock_gen.side_effect = RuntimeError("Synthetic generation failed")
        
        with patch('data.validate_raw.write_state_decision'):
            with patch('data.validate_raw.log_fallback_decision'):
                result = validate_raw_directory(raw_dir)
    
    assert result["status"] == "fail"
    assert len(result["missing_vars"]) > 0