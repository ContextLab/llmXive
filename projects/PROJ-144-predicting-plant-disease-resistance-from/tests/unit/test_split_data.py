import os
import json
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Mock the constants to use temporary directories for testing
import sys
from unittest.mock import patch, MagicMock

# Add code to path if not already present
if 'code' not in sys.path:
    sys.path.insert(0, 'code')

from modeling.split_data import load_processed_data, split_data

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory structure mimicking DATA_PROCESSED_DIR"""
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    return processed_dir

@pytest.fixture
def small_sample_data(temp_data_dir):
    """Create a small dataset (N < 50)"""
    n_samples = 20
    n_features = 5
    
    # Create dummy matrix
    X = pd.DataFrame(
        np.random.rand(n_samples, n_features),
        columns=[f'metabolite_{i}' for i in range(n_features)],
        index=[f'sample_{i}' for i in range(n_samples)]
    )
    
    # Create dummy labels with binary labels
    y = pd.DataFrame({
        'binary_label': np.random.choice([0, 1], n_samples)
    }, index=X.index)
    
    # Save to temp dir
    X.to_csv(temp_data_dir / "batch_corrected_matrix.csv")
    y.to_csv(temp_data_dir / "labels.csv")
    
    return str(temp_data_dir), n_samples

@pytest.fixture
def large_sample_data(temp_data_dir):
    """Create a large dataset (N >= 50)"""
    n_samples = 60
    n_features = 5
    
    # Create dummy matrix
    X = pd.DataFrame(
        np.random.rand(n_samples, n_features),
        columns=[f'metabolite_{i}' for i in range(n_features)],
        index=[f'sample_{i}' for i in range(n_samples)]
    )
    
    # Create dummy labels with balanced binary labels for stratification
    labels = [0] * 30 + [1] * 30
    np.random.shuffle(labels)
    y = pd.DataFrame({
        'binary_label': labels
    }, index=X.index)
    
    # Save to temp dir
    X.to_csv(temp_data_dir / "batch_corrected_matrix.csv")
    y.to_csv(temp_data_dir / "labels.csv")
    
    return str(temp_data_dir), n_samples

def test_split_small_dataset(small_sample_data, temp_data_dir):
    """Test that small datasets trigger learning curve config"""
    import numpy as np
    data_dir, n_samples = small_sample_data
    
    # Patch the DATA_PROCESSED_DIR constant
    with patch('modeling.split_data.DATA_PROCESSED_DIR', data_dir):
        X, y = load_processed_data()
        output_file = split_data(X, y)
        
        # Verify output file exists
        assert os.path.exists(output_file)
        
        # Verify content
        with open(output_file, 'r') as f:
            config = json.load(f)
        
        assert 'fractions' in config
        assert 'learning_curve_subsample' == config['method']
        assert config['n_total'] == n_samples
        assert 'holdout_indices' not in config

def test_split_large_dataset(large_sample_data, temp_data_dir):
    """Test that large datasets trigger hold-out split"""
    import numpy as np
    data_dir, n_samples = large_sample_data
    
    # Patch the DATA_PROCESSED_DIR constant
    with patch('modeling.split_data.DATA_PROCESSED_DIR', data_dir):
        X, y = load_processed_data()
        output_file = split_data(X, y)
        
        # Verify output file exists
        assert os.path.exists(output_file)
        
        # Verify content
        with open(output_file, 'r') as f:
            split_data_result = json.load(f)
        
        assert 'train_indices' in split_data_result
        assert 'holdout_indices' in split_data_result
        assert 'stratified_holdout' == split_data_result['method']
        assert len(split_data_result['train_indices']) + len(split_data_result['holdout_indices']) == n_samples
        
        # Verify stratification is preserved (approximate check)
        train_labels = y.loc[split_data_result['train_indices']]['binary_label']
        holdout_labels = y.loc[split_data_result['holdout_indices']]['binary_label']
        
        # Both sets should have both classes
        assert set(train_labels.unique()) == {0, 1}
        assert set(holdout_labels.unique()) == {0, 1}

def test_missing_input_files(temp_data_dir):
    """Test that missing input files raise FileNotFoundError"""
    # Ensure files don't exist
    if (temp_data_dir / "batch_corrected_matrix.csv").exists():
        (temp_data_dir / "batch_corrected_matrix.csv").unlink()
    
    with patch('modeling.split_data.DATA_PROCESSED_DIR', str(temp_data_dir)):
        with pytest.raises(FileNotFoundError):
            load_processed_data()

def test_missing_label_column(temp_data_dir):
    """Test that missing binary label column raises ValueError"""
    import numpy as np
    
    # Create data without binary_label column
    X = pd.DataFrame(
        np.random.rand(10, 3),
        columns=['m1', 'm2', 'm3'],
        index=[f's{i}' for i in range(10)]
    )
    y = pd.DataFrame({
        'other_col': np.random.rand(10)
    }, index=X.index)
    
    X.to_csv(temp_data_dir / "batch_corrected_matrix.csv")
    y.to_csv(temp_data_dir / "labels.csv")
    
    with patch('modeling.split_data.DATA_PROCESSED_DIR', str(temp_data_dir)):
        with pytest.raises(ValueError):
            load_processed_data()