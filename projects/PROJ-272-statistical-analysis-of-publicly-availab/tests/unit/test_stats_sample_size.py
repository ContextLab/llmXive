import pytest
import pandas as pd
import json
import os
from pathlib import Path
from unittest.mock import patch, mock_open

# Mock config paths for testing
@pytest.fixture
def mock_config_paths():
    with patch('config.get_path') as mock_get_path:
        def side_effect(key):
            if key == "data/results/metadata.json":
                return Path("/tmp/test_metadata.json")
            return Path("/tmp/fake_path")
        mock_get_path.side_effect = side_effect
        yield mock_get_path

@pytest.fixture
def small_dataset():
    """Create a dataset with one group having < 10 participants."""
    data = {
        "participant_id": [f"p{i}" for i in range(15)],
        "label": ["Control"] * 5 + ["AD"] * 10,  # Control group is small
        "TTR": [0.5] * 15,
        "MTLD": [50.0] * 15
    }
    return pd.DataFrame(data)

@pytest.fixture
def sufficient_dataset():
    """Create a dataset with sufficient participants in all groups."""
    data = {
        "participant_id": [f"p{i}" for i in range(30)],
        "label": ["Control"] * 15 + ["AD"] * 15,
        "TTR": [0.5] * 30,
        "MTLD": [50.0] * 30
    }
    return pd.DataFrame(data)

def test_check_sample_sizes_low_power(small_dataset, mock_config_paths, tmp_path):
    """Test that low power is detected and logged when group < 10."""
    # Patch the metadata path to a temporary file
    metadata_file = tmp_path / "metadata.json"
    
    with patch('stats.get_path', return_value=str(metadata_file)), \
         patch('stats.ensure_dirs'), \
         patch('stats.logger') as mock_logger:
        
        from stats import check_sample_sizes
        
        result = check_sample_sizes(small_dataset, threshold=10)
        
        assert result["low_power"] is True
        assert len(result["low_power_groups"]) > 0
        
        # Verify warning was logged
        warning_calls = [call for call in mock_logger.warning.call_args_list if "Low sample size" in str(call)]
        assert len(warning_calls) > 0

def test_check_sample_sizes_sufficient(sufficient_dataset, mock_config_paths, tmp_path):
    """Test that low power is NOT detected when groups >= 10."""
    metadata_file = tmp_path / "metadata.json"
    
    with patch('stats.get_path', return_value=str(metadata_file)), \
         patch('stats.ensure_dirs'), \
         patch('stats.logger') as mock_logger:
        
        from stats import check_sample_sizes
        
        result = check_sample_sizes(sufficient_dataset, threshold=10)
        
        assert result["low_power"] is False
        assert "group_counts" in result
        
        # Verify no low power warning was logged
        warning_calls = [call for call in mock_logger.warning.call_args_list if "Low sample size" in str(call)]
        assert len(warning_calls) == 0

def test_metadata_file_updated(small_dataset, mock_config_paths, tmp_path):
    """Test that the metadata file is actually written with the low_power flag."""
    metadata_file = tmp_path / "metadata.json"
    
    with patch('stats.get_path', return_value=str(metadata_file)), \
         patch('stats.ensure_dirs'):
        
        from stats import check_sample_sizes
        
        check_sample_sizes(small_dataset, threshold=10)
        
        assert metadata_file.exists()
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        assert metadata["low_power"] is True