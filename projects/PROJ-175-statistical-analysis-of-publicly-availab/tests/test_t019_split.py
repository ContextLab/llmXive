"""
Tests for T019: Train/Test Split
"""
import os
import json
import tempfile
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.data.split import load_subset_size, create_train_test_split, SEED

@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        data_dir = tmp_path / "data"
        processed_dir = data_dir / "processed"
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        yield {
            "base": tmp_path,
            "data": data_dir,
            "processed": processed_dir
        }

@pytest.fixture
def mock_power_analysis(temp_dirs):
    """Create a mock power_analysis.json with N_unified."""
    config = {
        "N_unified": 1000,
        "effect_size": 0.1,
        "power": 0.8
    }
    file_path = temp_dirs["data"] / "power_analysis.json"
    with open(file_path, 'w') as f:
        json.dump(config, f)
    return config

@pytest.fixture
def mock_input_data(temp_dirs):
    """Create a mock final_features.parquet with enough data."""
    data = {
        "ingredient_id": range(1200),
        "log_co_occurrence": [0.5] * 1200,
        "flavor_similarity": [0.3] * 1200,
        "functional_role": [0] * 1200,
        "compatibility_label": [0, 1] * 600  # Balanced for stratification
    }
    df = pd.DataFrame(data)
    file_path = temp_dirs["processed"] / "final_features.parquet"
    df.to_parquet(file_path, index=False)
    return df

def test_load_subset_size(mock_power_analysis, temp_dirs):
    """Test loading N_unified from power analysis file."""
    # Patch the global path variables
    with patch('code.data.split.POWER_ANALYSIS_FILE', mock_power_analysis["base"] / "data" / "power_analysis.json"):
        size = load_subset_size()
        assert size == 1000

def test_load_subset_size_missing_file(temp_dirs):
    """Test error handling when power analysis file is missing."""
    with patch('code.data.split.POWER_ANALYSIS_FILE', temp_dirs["data"] / "nonexistent.json"):
        with pytest.raises(FileNotFoundError):
            load_subset_size()

def test_load_subset_size_missing_key(temp_dirs, mock_power_analysis):
    """Test error handling when N_unified is missing."""
    # Overwrite file with missing key
    config_path = mock_power_analysis["base"] / "data" / "power_analysis.json"
    with open(config_path, 'w') as f:
        json.dump({"other_key": 123}, f)
    
    with patch('code.data.split.POWER_ANALYSIS_FILE', config_path):
        with pytest.raises(KeyError):
            load_subset_size()

def test_create_train_test_split(mock_power_analysis, mock_input_data, temp_dirs):
    """Test the full split workflow."""
    # Patch paths
    data_path = temp_dirs["data"]
    proc_path = temp_dirs["processed"]
    
    with patch('code.data.split.POWER_ANALYSIS_FILE', data_path / "power_analysis.json"):
        with patch('code.data.split.DATA_DIR', data_path):
            with patch('code.data.split.PROCESSED_DIR', proc_path):
                with patch('code.data.split.INPUT_FILE', proc_path / "final_features.parquet"):
                    with patch('code.data.split.TRAIN_OUTPUT', proc_path / "train_set.parquet"):
                        with patch('code.data.split.TEST_OUTPUT', proc_path / "test_set.parquet"):
                            with patch('code.data.split.SPLIT_CONFIG_FILE', data_path / "split_config.json"):
                                result = create_train_test_split()
    
    # Verify outputs exist
    assert (proc_path / "train_set.parquet").exists()
    assert (proc_path / "test_set.parquet").exists()
    assert (data_path / "split_config.json").exists()
    
    # Verify split config content
    with open(data_path / "split_config.json", 'r') as f:
        config = json.load(f)
    
    assert config["train_size"] + config["test_size"] <= 1000
    assert abs(config["train_ratio"] - 0.8) < 0.05
    assert config["seed"] == SEED
    assert config["stratified"] is True
    
    # Verify data integrity
    train_df = pd.read_parquet(proc_path / "train_set.parquet")
    test_df = pd.read_parquet(proc_path / "test_set.parquet")
    
    assert len(train_df) + len(test_df) <= 1000
    assert "compatibility_label" in train_df.columns
    assert "compatibility_label" in test_df.columns
    
    # Verify stratification maintained (roughly)
    train_ratio = train_df['compatibility_label'].mean()
    test_ratio = test_df['compatibility_label'].mean()
    assert abs(train_ratio - test_ratio) < 0.1  # Should be close due to stratification
