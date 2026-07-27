import os
import sys
import json
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.data.split import load_subset_size, create_train_test_split

@pytest.fixture
def mock_power_analysis(tmp_path):
    """Create a mock power_analysis.json"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    power_file = data_dir / "power_analysis.json"
    power_file.write_text(json.dumps({"N_unified": 100}))
    return data_dir

@pytest.fixture
def mock_final_features(tmp_path):
    """Create a mock final_features.parquet with enough rows"""
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    
    # Create a DataFrame with required columns
    df = pd.DataFrame({
        'ingredient_id': range(200),
        'log_co_occurrence': np.random.rand(200),
        'flavor_similarity': np.random.rand(200),
        'functional_role': np.random.choice(['A', 'B', 'C'], 200),
        'compatibility_label': np.random.choice([0, 1], 200)
    })
    
    file_path = data_dir / "final_features.parquet"
    df.to_parquet(file_path)
    return file_path

@pytest.fixture
def mock_project_root(tmp_path, mock_power_analysis, mock_final_features):
    """Set up the directory structure and mock PROJECT_ROOT in the module"""
    # Move files to expected locations relative to tmp_path
    # tmp_path structure:
    # tmp_path/
    #   data/
    #     power_analysis.json
    #     processed/
    #       final_features.parquet
    
    # Patch the PROJECT_ROOT in the split module
    import code.data.split as split_module
    
    original_root = split_module.PROJECT_ROOT
    split_module.PROJECT_ROOT = tmp_path
    
    yield tmp_path
    
    # Restore original root
    split_module.PROJECT_ROOT = original_root

def test_load_subset_size(mock_project_root):
    """Test loading N_unified from power_analysis.json"""
    size = load_subset_size()
    assert size == 100
    assert isinstance(size, int)

def test_create_train_test_split_downsamples(mock_project_root):
    """Test that the function downsamples to N_unified and splits correctly"""
    # Run the function
    create_train_test_split()
    
    # Check that output files exist
    processed_dir = mock_project_root / "data" / "processed"
    train_file = processed_dir / "train_set.parquet"
    test_file = processed_dir / "test_set.parquet"
    config_file = mock_project_root / "data" / "split_config.json"
    
    assert train_file.exists()
    assert test_file.exists()
    assert config_file.exists()
    
    # Load and verify sizes
    train_df = pd.read_parquet(train_file)
    test_df = pd.read_parquet(test_file)
    
    # N_unified is 100. 80/20 split -> 80 train, 20 test
    # Note: train_test_split with stratify might adjust slightly if labels are imbalanced,
    # but with 200 rows and random labels, it should be close.
    # Since we downsampled to 100 first:
    total_samples = len(train_df) + len(test_df)
    assert total_samples == 100
    
    # Check config
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    assert config['train_size'] == len(train_df)
    assert config['test_size'] == len(test_df)
    assert config['N_unified'] == 100
    assert config['random_seed'] == 42

def test_create_train_test_split_insufficient_data(mock_project_root, monkeypatch):
    """Test behavior when available data is less than N_unified"""
    # Create a smaller dataset
    data_dir = mock_project_root / "data" / "processed"
    df_small = pd.DataFrame({
        'ingredient_id': range(50),
        'log_co_occurrence': np.random.rand(50),
        'flavor_similarity': np.random.rand(50),
        'functional_role': np.random.choice(['A', 'B', 'C'], 50),
        'compatibility_label': np.random.choice([0, 1], 50)
    })
    df_small.to_parquet(data_dir / "final_features.parquet")
    
    # Run the function
    create_train_test_split()
    
    # Check outputs
    train_df = pd.read_parquet(data_dir / "train_set.parquet")
    test_df = pd.read_parquet(data_dir / "test_set.parquet")
    
    # Total should be 50 (all available data)
    assert len(train_df) + len(test_df) == 50

def test_missing_input_file(mock_project_root, monkeypatch):
    """Test that FileNotFoundError is raised if final_features.parquet is missing"""
    # Remove the input file
    input_file = mock_project_root / "data" / "processed" / "final_features.parquet"
    input_file.unlink()
    
    with pytest.raises(FileNotFoundError):
        create_train_test_split()

def test_missing_power_analysis(mock_project_root, monkeypatch):
    """Test that FileNotFoundError is raised if power_analysis.json is missing"""
    # Remove the power analysis file
    power_file = mock_project_root / "data" / "power_analysis.json"
    power_file.unlink()
    
    with pytest.raises(FileNotFoundError):
        load_subset_size()