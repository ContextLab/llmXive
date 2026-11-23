"""
Unit tests for validate_raw.py (Task T013a)
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
import pandas as pd
from unittest.mock import patch, MagicMock

# Ensure project root is in path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in os.sys.path:
    os.sys.path.insert(0, str(project_root))

from data.validate_raw import (
    validate_raw_directory,
    validate_raw_data_variables,
    REQUIRED_VARIABLES
)
from data.config import reset_config, get_config

@pytest.fixture
def temp_dirs():
    """Create temporary directories for raw and processed data."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        raw_dir = tmp_path / "data" / "raw"
        processed_dir = tmp_path / "data" / "processed"
        state_dir = tmp_path / "state"
        
        raw_dir.mkdir(parents=True)
        processed_dir.mkdir(parents=True)
        state_dir.mkdir(parents=True)
        
        # Mock config to use these temp dirs
        # We patch get_config to return a mock object with these paths
        mock_config = MagicMock()
        mock_config.paths.raw_data = raw_dir
        mock_config.paths.processed_data = processed_dir
        mock_config.paths.state = state_dir
        
        with patch('data.validate_raw.get_config', return_value=mock_config):
            with patch('data.download.get_config', return_value=mock_config):
                yield raw_dir, processed_dir, state_dir

def test_validate_raw_directory_empty(temp_dirs):
    """Test validation when raw directory is empty."""
    raw_dir, _, _ = temp_dirs
    assert validate_raw_directory(raw_dir) is False

def test_validate_raw_directory_with_csv(temp_dirs):
    """Test validation when raw directory has a CSV."""
    raw_dir, _, _ = temp_dirs
    test_file = raw_dir / "test.csv"
    test_file.write_text("col1,col2\n1,2")
    assert validate_raw_directory(raw_dir) is True

def test_validate_raw_data_variables_missing_vars(temp_dirs):
    """Test validation when required variables are missing."""
    raw_dir, processed_dir, _ = temp_dirs
    
    # Create a CSV with missing variables
    data = {
        "avatar_condition": [0, 1],
        "pre_self_esteem": [20.0, 22.0]
        # Missing post_self_esteem and comparison_tendency
    }
    df = pd.DataFrame(data)
    df.to_csv(raw_dir / "incomplete.csv", index=False)
    
    # We need to patch the synthetic generation to avoid actually creating files
    # or just verify the logic before the fallback triggers fully
    with patch('data.validate_raw._trigger_synthetic_fallback') as mock_fallback:
        result = validate_raw_data_variables(Path("data"))
        
        assert result["status"] == "fail"
        assert len(result["missing_vars"]) > 0
        assert "post_self_esteem" in result["missing_vars"]
        assert "comparison_tendency" in result["missing_vars"]
        mock_fallback.assert_called_once()

def test_validate_raw_data_variables_all_present(temp_dirs):
    """Test validation when all required variables are present."""
    raw_dir, processed_dir, _ = temp_dirs
    
    # Create a CSV with all required variables
    data = {
        "avatar_condition": [0, 1],
        "pre_self_esteem": [20.0, 22.0],
        "post_self_esteem": [21.0, 23.0],
        "comparison_tendency": [15.0, 16.0]
    }
    df = pd.DataFrame(data)
    df.to_csv(raw_dir / "complete.csv", index=False)
    
    # Mock the synthetic trigger to ensure it's not called
    with patch('data.validate_raw._trigger_synthetic_fallback') as mock_fallback:
        result = validate_raw_data_variables(Path("data"))
        
        assert result["status"] == "pass"
        assert result["missing_vars"] == []
        mock_fallback.assert_not_called()
        
        # Check that output file was written
        output_file = processed_dir / "pre_imputation_validation.json"
        assert output_file.exists()
        with open(output_file) as f:
            saved_result = json.load(f)
        assert saved_result["status"] == "pass"

def test_validate_raw_data_variables_no_files(temp_dirs):
    """Test validation when no CSV files exist."""
    raw_dir, processed_dir, _ = temp_dirs
    
    with patch('data.validate_raw._trigger_synthetic_fallback') as mock_fallback:
        result = validate_raw_data_variables(Path("data"))
        
        assert result["status"] == "fail"
        assert len(result["missing_vars"]) == len(REQUIRED_VARIABLES)
        mock_fallback.assert_called_once()