import os
import json
import tempfile
import shutil
import pandas as pd
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

# Mock config paths to avoid dependency on actual project structure during unit tests
@pytest.fixture(autouse=True)
def mock_config_paths(monkeypatch):
    temp_dir = tempfile.mkdtemp()
    data_dir = os.path.join(temp_dir, "data")
    raw_dir = os.path.join(data_dir, "raw")
    processed_dir = os.path.join(data_dir, "processed")
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)
    
    def mock_get_raw_data_dir(): return raw_dir
    def mock_get_processed_data_dir(): return processed_dir
    def mock_get_project_root(): return temp_dir
    def mock_get_random_seed(): return 42
    def mock_ensure_directories(): pass
    def mock_get_logger(name): 
        import logging
        return logging.getLogger(name)

    monkeypatch.setattr("data.preprocess.get_raw_data_dir", mock_get_raw_data_dir)
    monkeypatch.setattr("data.preprocess.get_processed_data_dir", mock_get_processed_data_dir)
    monkeypatch.setattr("data.preprocess.get_project_root", mock_get_project_root)
    monkeypatch.setattr("data.preprocess.get_random_seed", mock_get_random_seed)
    monkeypatch.setattr("data.preprocess.ensure_directories", mock_ensure_directories)
    monkeypatch.setattr("data.preprocess.get_logger", mock_get_logger)

from data.preprocess import save_normalization_bounds, detect_missing_values, compute_medians, impute_missing_values

def test_save_normalization_bounds(mock_config_paths):
    """Test T019: Save normalization bounds to JSON."""
    from sklearn.preprocessing import MinMaxScaler
    
    # Create dummy data
    X = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
    scaler = MinMaxScaler()
    scaler.fit(X)
    
    feature_names = ['laser_power', 'scan_speed']
    output_path = os.path.join(mock_config_paths, "data", "processed", "normalization_bounds.json")
    
    save_normalization_bounds(scaler, feature_names, output_path)
    
    # Verify file exists
    assert os.path.exists(output_path)
    
    # Verify content
    with open(output_path, 'r') as f:
        bounds = json.load(f)
    
    assert 'laser_power' in bounds
    assert 'scan_speed' in bounds
    assert bounds['laser_power']['min'] == 1.0
    assert bounds['laser_power']['max'] == 5.0
    assert bounds['scan_speed']['min'] == 2.0
    assert bounds['scan_speed']['max'] == 6.0

def test_detect_missing_values():
    df = pd.DataFrame({
        'A': [1, 2, np.nan],
        'B': [4, 5, 6],
        'C': [np.nan, np.nan, np.nan]
    })
    missing = detect_missing_values(df)
    assert 'A' in missing
    assert missing['A'] == 1
    assert 'C' in missing
    assert missing['C'] == 3

def test_compute_medians():
    df = pd.DataFrame({
        'A': [1, 2, 3, 4, 5],
        'B': [10, 20, 30, 40, 50]
    })
    medians = compute_medians(df, ['A', 'B'])
    assert medians['A'] == 3.0
    assert medians['B'] == 30.0

def test_impute_missing_values():
    df = pd.DataFrame({
        'A': [1, 2, np.nan],
        'B': [4, 5, 6]
    })
    medians = {'A': 2.0}
    df_imputed = impute_missing_values(df, medians)
    assert df_imputed['A'].iloc[2] == 2.0