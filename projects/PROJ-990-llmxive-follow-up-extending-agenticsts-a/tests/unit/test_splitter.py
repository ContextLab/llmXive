"""
Unit tests for the splitter module.
"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from splitter import (
    load_processed_data,
    stratified_split,
    train_test_split,
    save_split_data,
    validate_split,
    main
)
from config import load_config_from_file, ensure_directories

@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    np.random.seed(42)
    n_samples = 100
    
    data = {
        'trajectory_id': np.random.randint(1, 10, n_samples),
        'turn_id': np.random.randint(1, 20, n_samples),
        'utility_score': np.random.uniform(0, 1, n_samples),
        'health': np.random.randint(0, 100, n_samples),
        'threat': np.random.randint(0, 10, n_samples),
        'deck_size': np.random.randint(10, 50, n_samples)
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_stratified_split_continuous(sample_data):
    """Test stratified split with continuous utility scores."""
    train_df, holdout_df = stratified_split(
        sample_data,
        stratify_column='utility_score',
        test_size=0.2,
        random_state=42
    )
    
    # Check sizes
    assert len(train_df) + len(holdout_df) == len(sample_data)
    assert len(holdout_df) == int(len(sample_data) * 0.2)
    
    # Check that utility_score exists in both
    assert 'utility_score' in train_df.columns
    assert 'utility_score' in holdout_df.columns

def test_stratified_split_categorical():
    """Test stratified split with categorical data."""
    np.random.seed(42)
    n_samples = 100
    
    data = {
        'id': range(n_samples),
        'category': np.random.choice(['A', 'B', 'C'], n_samples),
        'value': np.random.uniform(0, 1, n_samples)
    }
    df = pd.DataFrame(data)
    
    train_df, holdout_df = stratified_split(
        df,
        stratify_column='category',
        test_size=0.2,
        random_state=42
    )
    
    # Check that category distribution is similar
    train_dist = train_df['category'].value_counts(normalize=True).sort_index()
    holdout_dist = holdout_df['category'].value_counts(normalize=True).sort_index()
    
    # Allow some tolerance for randomness
    for cat in ['A', 'B', 'C']:
        train_prop = train_dist.get(cat, 0)
        holdout_prop = holdout_dist.get(cat, 0)
        assert abs(train_prop - holdout_prop) < 0.1, f"Distribution mismatch for {cat}"

def test_train_test_split_custom(sample_data):
    """Test custom train-test split implementation."""
    train_df, test_df = train_test_split(
        sample_data,
        test_size=0.2,
        stratify=sample_data['utility_score'],
        random_state=42
    )
    
    assert len(train_df) + len(test_df) == len(sample_data)
    assert len(test_df) == int(len(sample_data) * 0.2)

def test_validate_split(sample_data):
    """Test split validation."""
    train_df, holdout_df = stratified_split(
        sample_data,
        stratify_column='utility_score',
        test_size=0.2,
        random_state=42
    )
    
    report = validate_split(train_df, holdout_df)
    
    assert 'train_size' in report
    assert 'holdout_size' in report
    assert 'train_mean' in report
    assert 'holdout_mean' in report
    assert 'distribution_match' in report
    assert report['distribution_match'] is True

def test_save_split_data(sample_data, temp_dir):
    """Test saving split data to CSV."""
    train_df, holdout_df = stratified_split(
        sample_data,
        stratify_column='utility_score',
        test_size=0.2,
        random_state=42
    )
    
    save_split_data(train_df, holdout_df, temp_dir)
    
    train_path = Path(temp_dir) / 'train_set.csv'
    holdout_path = Path(temp_dir) / 'holdout_set.csv'
    
    assert train_path.exists()
    assert holdout_path.exists()
    
    # Verify content
    loaded_train = pd.read_csv(train_path)
    loaded_holdout = pd.read_csv(holdout_path)
    
    assert len(loaded_train) == len(train_df)
    assert len(loaded_holdout) == len(holdout_df)

def test_main_with_mock_data(temp_dir):
    """Test main function with mock data."""
    # Create mock input files
    utility_labels = pd.DataFrame({
        'trajectory_id': [1, 2, 3, 4, 5],
        'turn_id': [1, 1, 1, 1, 1],
        'utility_score': [0.1, 0.2, 0.3, 0.4, 0.5]
    })
    utility_path = Path(temp_dir) / 'utility_labels.csv'
    utility_labels.to_csv(utility_path, index=False)
    
    parser_metrics = pd.DataFrame({
        'trajectory_id': [1, 2, 3, 4, 5],
        'turn_id': [1, 1, 1, 1, 1],
        'health': [100, 90, 80, 70, 60],
        'threat': [1, 2, 3, 4, 5],
        'deck_size': [20, 25, 30, 35, 40]
    })
    metrics_path = Path(temp_dir) / 'parser_metrics.csv'
    parser_metrics.to_csv(metrics_path, index=False)
    
    # Create a minimal config
    config = {
        'paths': {
            'utility_labels': str(utility_path),
            'parser_metrics': str(metrics_path),
            'processed': temp_dir
        },
        'hyperparameters': {
            'random_state': 42
        }
    }
    
    config_path = Path(temp_dir) / 'config.json'
    with open(config_path, 'w') as f:
        json.dump(config, f)
    
    # Mock load_config_from_file to return our config
    original_func = load_config_from_file
    import splitter
    splitter.load_config_from_file = lambda: config
    splitter.ensure_directories = lambda c: None
    
    try:
        main()
        
        # Check outputs
        train_path = Path(temp_dir) / 'train_set.csv'
        holdout_path = Path(temp_dir) / 'holdout_set.csv'
        report_path = Path(temp_dir) / 'split_validation_report.json'
        
        assert train_path.exists()
        assert holdout_path.exists()
        assert report_path.exists()
    finally:
        # Restore original function
        splitter.load_config_from_file = original_func