"""
Tests for T015: Data Splitting Logic

Verifies that the training script correctly loads the dataset,
validates schema, performs stratified splitting, and saves outputs.
"""
import os
import sys
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd
import numpy as np

# Add code/ to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.train import (
    load_final_dataset,
    validate_dataset_schema,
    split_data,
    save_splits,
    main
)
from config import reset_config, get_paths


@pytest.fixture
def mock_dataset():
    """Create a mock dataset with required columns."""
    data = {
        'composition_id': [f'ID_{i}' for i in range(24)],
        'chemical_family': ['oxide'] * 8 + ['sulfide'] * 8 + ['organic'] * 8,
        'Tg': [np.random.uniform(300, 500) for _ in range(24)],
        'crystallization_label': np.random.randint(0, 2, 24),
        'rdf_peak_pos': np.random.uniform(2.0, 3.0, 24),
        'rdf_peak_width': np.random.uniform(0.1, 0.5, 24),
        'bond_angle_variance': np.random.uniform(0.0, 10.0, 24),
        'coordination_numbers': np.random.uniform(4.0, 6.0, 24)
    }
    return pd.DataFrame(data)


@pytest.fixture
def temp_data_dir(mock_dataset):
    """Create a temporary directory structure and save mock data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        data_processed = tmpdir / 'data' / 'processed'
        data_processed.mkdir(parents=True)
        
        # Save mock dataset
        dataset_path = data_processed / 'final_dataset.parquet'
        mock_dataset.to_parquet(dataset_path)
        
        # Patch get_paths to return this temp directory
        original_get_paths = get_paths
        
        def mock_get_paths():
            paths = MagicMock()
            paths.data_processed = data_processed
            return paths
        
        with patch('models.train.get_paths', mock_get_paths):
            yield tmpdir, mock_dataset


def test_load_final_dataset_success(temp_data_dir, mock_dataset):
    """Test successful loading of final dataset."""
    tmpdir, _ = temp_data_dir
    df = load_final_dataset()
    assert len(df) == len(mock_dataset)
    assert 'Tg' in df.columns
    assert 'chemical_family' in df.columns


def test_load_final_dataset_missing_file():
    """Test failure when final dataset is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        data_processed = tmpdir / 'data' / 'processed'
        data_processed.mkdir(parents=True)
        
        with patch('models.train.get_paths') as mock_paths:
            mock_paths.return_value.data_processed = data_processed
            with pytest.raises(FileNotFoundError, match="FATAL: Final dataset not found"):
                load_final_dataset()


def test_validate_dataset_schema_success(mock_dataset):
    """Test schema validation with valid data."""
    # Should not raise
    validate_dataset_schema(mock_dataset)


def test_validate_dataset_schema_missing_column(mock_dataset):
    """Test schema validation failure when column is missing."""
    df = mock_dataset.drop(columns=['Tg'])
    with pytest.raises(ValueError, match="missing required columns"):
        validate_dataset_schema(df)


def test_split_data_stratified(mock_dataset):
    """Test stratified split."""
    train_df, test_df, stats = split_data(mock_dataset)
    
    # Check sizes
    assert len(train_df) + len(test_df) == len(mock_dataset)
    assert len(test_df) == int(len(mock_dataset) * 0.2)
    
    # Check stratification roughly preserved
    train_families = train_df['chemical_family'].value_counts()
    test_families = test_df['chemical_family'].value_counts()
    
    # Since we have 8 of each, and 20% test, we expect ~1-2 per family in test
    # Exact counts depend on random state, but distribution should be similar
    assert set(train_families.index) == set(mock_dataset['chemical_family'].unique())
    assert set(test_families.index) == set(mock_dataset['chemical_family'].unique())


def test_split_data_nan_handling(mock_dataset):
    """Test that rows with NaN targets are dropped."""
    df_nan = mock_dataset.copy()
    df_nan.loc[0, 'Tg'] = np.nan
    
    train_df, test_df, stats = split_data(df_nan)
    
    # Row 0 should be dropped
    assert len(train_df) + len(test_df) == len(mock_dataset) - 1
    assert 'rows_after_dropping_nan' in stats
    assert stats['rows_after_dropping_nan'] == len(mock_dataset) - 1


def test_save_splits(temp_data_dir, mock_dataset):
    """Test saving split data."""
    tmpdir, _ = temp_data_dir
    df = mock_dataset
    train_df, test_df, stats = split_data(df)
    
    paths = get_paths()
    splits_dir = paths.data_processed / 'splits'
    
    save_splits(train_df, test_df, stats)
    
    assert (splits_dir / 'train_set.parquet').exists()
    assert (splits_dir / 'test_set.parquet').exists()
    assert (splits_dir / 'split_statistics.json').exists()
    
    # Verify content
    with open(splits_dir / 'split_statistics.json') as f:
        loaded_stats = json.load(f)
    assert loaded_stats['train_size'] == len(train_df)
    assert loaded_stats['test_size'] == len(test_df)


def test_main_integration(temp_data_dir, mock_dataset):
    """Test the full main flow."""
    result = main()
    assert result == 0
    
    paths = get_paths()
    splits_dir = paths.data_processed / 'splits'
    assert (splits_dir / 'train_set.parquet').exists()
    assert (splits_dir / 'test_set.parquet').exists()