"""
Unit tests for the validity check module (T019).
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import os
from unittest.mock import patch, MagicMock

# Mock config to avoid file system dependencies in unit tests
@pytest.fixture
def mock_config(tmp_path):
    """Mock the config.get_path function to use temporary directories."""
    with patch('code.utils.validity_check.get_path') as mock_get_path:
        # Setup mock paths
        data_dir = tmp_path / "data" / "processed"
        data_dir.mkdir(parents=True)
        artifacts_dir = tmp_path / "artifacts"
        artifacts_dir.mkdir(parents=True)
        
        def side_effect(path_str):
            if "unified_analysis.csv" in path_str:
                return data_dir / "unified_analysis.csv"
            elif "results.json" in path_str:
                return artifacts_dir / "results.json"
            return tmp_path / path_str
        
        mock_get_path.side_effect = side_effect
        yield mock_get_path

@pytest.fixture
def sample_dataframe():
    """Create a sample dataframe for testing."""
    data = {
        'image_path': [f'image_{i}.jpg' for i in range(100)],
        'disease_label': ['healthy'] * 50 + ['diseased'] * 50,
        'lesion_area_ratio': np.random.rand(100),
        'necrosis_color_index': np.random.rand(100),
        'texture_entropy': np.random.rand(100),
        'location_lat': [40.0] * 100,
        'location_lon': [-75.0] * 100,
        'image_date': ['2023-01-01'] * 100
    }
    return pd.DataFrame(data)

@pytest.fixture
def empty_dataframe():
    """Create an empty dataframe."""
    return pd.DataFrame(columns=['image_path', 'disease_label'])

def test_load_unified_dataset_success(mock_config, sample_dataframe, tmp_path):
    """Test successful loading of the dataset."""
    # Save sample data
    data_path = tmp_path / "data" / "processed" / "unified_analysis.csv"
    sample_dataframe.to_csv(data_path, index=False)
    
    from code.utils.validity_check import load_unified_dataset
    
    df = load_unified_dataset()
    assert len(df) == 100
    assert 'lesion_area_ratio' in df.columns

def test_load_unified_dataset_not_found(mock_config, tmp_path):
    """Test loading when file does not exist."""
    from code.utils.validity_check import load_unified_dataset
    
    with pytest.raises(FileNotFoundError):
        load_unified_dataset()

def test_load_unified_dataset_empty(mock_config, empty_dataframe, tmp_path):
    """Test loading when dataset is empty."""
    data_path = tmp_path / "data" / "processed" / "unified_analysis.csv"
    empty_dataframe.to_csv(data_path, index=False)
    
    from code.utils.validity_check import load_unified_dataset
    
    with pytest.raises(ValueError):
        load_unified_dataset()

def test_sample_random_subset(sample_dataframe):
    """Test random sampling logic."""
    from code.utils.validity_check import sample_random_subset
    
    subset = sample_random_subset(sample_dataframe, n=10, seed=42)
    assert len(subset) == 10
    assert subset.equals(sample_dataframe.sample(n=10, random_state=42))
    
    # Test edge case: n >= len(df)
    subset_full = sample_random_subset(sample_dataframe, n=200, seed=42)
    assert len(subset_full) == 100

def test_check_construct_validity_no_ground_truth(sample_dataframe):
    """Test that validity check correctly flags 'Associational Only'."""
    from code.utils.validity_check import check_construct_validity
    
    subset = sample_dataframe.sample(n=10, random_state=42)
    results = check_construct_validity(subset)
    
    assert results['validity_passed'] is True
    assert results['flag'] == 'Associational Only'
    assert results['correlation_value'] is None
    assert 'no ground truth' in results['reason'].lower()

def test_check_construct_validity_missing_columns(sample_dataframe):
    """Test validity check with missing required columns."""
    from code.utils.validity_check import check_construct_validity
    
    # Remove a required column
    subset = sample_dataframe.drop(columns=['lesion_area_ratio']).sample(n=10, random_state=42)
    results = check_construct_validity(subset)
    
    assert results['validity_passed'] is False
    assert 'Missing columns' in results['reason']

def test_update_results_json(mock_config, sample_dataframe, tmp_path):
    """Test updating the results.json file."""
    from code.utils.validity_check import update_results_json, check_construct_validity
    
    subset = sample_dataframe.sample(n=10, random_state=42)
    results = check_construct_validity(subset)
    
    update_results_json(results)
    
    results_path = tmp_path / "artifacts" / "results.json"
    assert results_path.exists()
    
    with open(results_path, 'r') as f:
        saved_results = json.load(f)
    
    assert 'validity_check' in saved_results
    assert saved_results['validity_check']['flag'] == 'Associational Only'
    assert saved_results.get('study_type') == 'Observational (Associational Only)'

def test_run_validity_check_integration(mock_config, sample_dataframe, tmp_path):
    """Integration test for the full validity check pipeline."""
    # Setup data file
    data_path = tmp_path / "data" / "processed" / "unified_analysis.csv"
    sample_dataframe.to_csv(data_path, index=False)
    
    from code.utils.validity_check import run_validity_check, update_results_json
    
    success, results = run_validity_check(seed=42)
    
    assert success is True
    assert results['flag'] == 'Associational Only'
    
    # Verify results.json was updated
    update_results_json(results)
    results_path = tmp_path / "artifacts" / "results.json"
    assert results_path.exists()