import os
import json
import tempfile
import shutil
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# We need to mock the config paths or set up a temporary environment
# Since we cannot easily change global config in a test without side effects,
# we will test the full flow by creating a temporary directory structure
# and patching the config functions if possible, or by running the script
# in a controlled environment.

# For this integration test, we assume the config is set to a temp dir
# or we test the functions that write to specific relative paths if the
# environment is set up.

# Given the constraints, we will simulate the full pipeline execution
# by creating a mock raw data file and running the main logic.

# Note: In a real CI, we would set environment variables or mock the config module.
# Here we assume the config functions return paths relative to a temp root.

import code.config as config_module
from data.preprocess import validate_and_preprocess, save_normalization_bounds
from sklearn.preprocessing import MinMaxScaler

@pytest.fixture
def temp_project_root():
    tmpdir = tempfile.mkdtemp()
    # Create necessary subdirectories
    os.makedirs(os.path.join(tmpdir, "data", "raw"))
    os.makedirs(os.path.join(tmpdir, "data", "processed"))
    os.makedirs(os.path.join(tmpdir, "contracts"))
    os.makedirs(os.path.join(tmpdir, "results"))
    os.makedirs(os.path.join(tmpdir, "logs"))
    
    # Create a mock raw CSV
    csv_path = os.path.join(tmpdir, "data", "raw", "am_data.csv")
    data = {
        'laser_power': [200, 250, 300, 350, 400, 220, 280, 320],
        'scan_speed': [100, 120, 140, 160, 180, 110, 130, 150],
        'layer_thickness': [0.03, 0.03, 0.03, 0.03, 0.03, 0.05, 0.05, 0.05],
        'alloy_type': ['Al', 'Al', 'Ti', 'Ti', 'Ti', 'Al', 'Al', 'Ti'],
        'yield_strength': [300, 320, 350, 380, 400, 310, 340, 370],
        'ductility': [10, 12, 8, 6, 5, 11, 9, 7]
    }
    pd.DataFrame(data).to_csv(csv_path, index=False)
    
    # Create mock schema
    schema_path = os.path.join(tmpdir, "contracts", "dataset.schema.yaml")
    schema = {
        "required_columns": ["laser_power", "scan_speed", "layer_thickness", "yield_strength", "ductility"],
        "optional_columns": ["fatigue_life"],
        "column_types": {
            "laser_power": "numeric",
            "scan_speed": "numeric",
            "layer_thickness": "numeric",
            "alloy_type": "categorical",
            "yield_strength": "numeric",
            "ductility": "numeric"
        }
    }
    # We need a simple YAML writer or just a mock that passes
    # Since schema_validator might expect specific YAML, we'll create a minimal valid one
    with open(schema_path, 'w') as f:
        f.write("required_columns: [laser_power, scan_speed, layer_thickness, yield_strength, ductility]\n")
        f.write("optional_columns: [fatigue_life]\n")
        f.write("column_types:\n")
        f.write("  laser_power: numeric\n")
        f.write("  scan_speed: numeric\n")
        f.write("  layer_thickness: numeric\n")
        f.write("  alloy_type: categorical\n")
        f.write("  yield_strength: numeric\n")
        f.write("  ductility: numeric\n")

    # Create excluded_columns.yaml
    excluded_path = os.path.join(tmpdir, "data", "processed", "excluded_columns.yaml")
    with open(excluded_path, 'w') as f:
        f.write("excluded_columns: []\n")

    # Patch config functions to use temp dir
    original_get_project_root = config_module.get_project_root
    original_get_raw_data_dir = config_module.get_raw_data_dir
    original_get_processed_data_dir = config_module.get_processed_data_dir
    original_get_logs_dir = config_module.get_logs_dir
    original_get_contracts_dir = config_module.get_contracts_dir

    config_module.get_project_root = lambda: tmpdir
    config_module.get_raw_data_dir = lambda: os.path.join(tmpdir, "data", "raw")
    config_module.get_processed_data_dir = lambda: os.path.join(tmpdir, "data", "processed")
    config_module.get_logs_dir = lambda: os.path.join(tmpdir, "logs")
    config_module.get_contracts_dir = lambda: os.path.join(tmpdir, "contracts")
    
    yield tmpdir

    # Restore
    config_module.get_project_root = original_get_project_root
    config_module.get_raw_data_dir = original_get_raw_data_dir
    config_module.get_processed_data_dir = original_get_processed_data_dir
    config_module.get_logs_dir = original_get_logs_dir
    config_module.get_contracts_dir = original_get_contracts_dir
    
    shutil.rmtree(tmpdir)

def test_full_preprocessing_pipeline(temp_project_root):
    """Test the full preprocessing pipeline end-to-end."""
    # Run the main validation and preprocessing
    result = validate_and_preprocess()
    
    # Check that normalization bounds were saved
    bounds_path = os.path.join(temp_project_root, "data", "processed", "normalization_bounds.json")
    assert os.path.exists(bounds_path), "normalization_bounds.json was not created"
    
    with open(bounds_path, 'r') as f:
        bounds = json.load(f)
    
    assert 'feature_columns' in bounds
    assert 'min_values' in bounds
    assert 'max_values' in bounds
    assert len(bounds['feature_columns']) > 0
    
    # Check that processed CSVs were created
    train_path = os.path.join(temp_project_root, "data", "processed", "am_data_train.csv")
    test_path = os.path.join(temp_project_root, "data", "processed", "am_data_test.csv")
    
    assert os.path.exists(train_path), "Train CSV was not created"
    assert os.path.exists(test_path), "Test CSV was not created"
    
    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)
    
    assert len(train_df) > 0
    assert len(test_df) > 0
    assert 'yield_strength' in train_df.columns
    assert 'ductility' in train_df.columns