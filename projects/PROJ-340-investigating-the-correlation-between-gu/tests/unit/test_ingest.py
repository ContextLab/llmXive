import os
import sys
import json
import yaml
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
import tempfile
import shutil

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from ingest import (
    validate_variables,
    save_variable_metrics,
    detect_outliers_iqr,
    filter_outliers,
    calculate_checksum,
    register_checksum_in_state
)

def test_validate_variables_success():
    """Test validation when all required variables are present."""
    # Create a mock DataFrame
    df = pd.DataFrame({
        'taxa_a': [1, 2, 3],
        'taxa_b': [4, 5, 6],
        'sleep_duration': [7.5, 8.0, 6.5]
    })
    
    required_vars = {
        'predictors': ['taxa_a', 'taxa_b'],
        'outcomes': ['sleep_duration']
    }
    
    metrics = validate_variables(df, required_vars)
    
    assert metrics['percentage_loaded'] == 100.0
    assert metrics['missing_count'] == 0
    assert metrics['missing_variables'] == []
    assert os.path.exists('data/results/variable_load_metrics.json')

def test_validate_variables_missing():
    """Test validation when some required variables are missing."""
    df = pd.DataFrame({
        'taxa_a': [1, 2, 3],
        'sleep_duration': [7.5, 8.0, 6.5]
    })
    
    required_vars = {
        'predictors': ['taxa_a', 'taxa_b'],
        'outcomes': ['sleep_duration']
    }
    
    metrics = validate_variables(df, required_vars)
    
    assert metrics['percentage_loaded'] < 100.0
    assert 'taxa_b' in metrics['missing_variables']
    assert metrics['missing_count'] == 1

def test_detect_outliers_iqr():
    """Test IQR outlier detection."""
    df = pd.DataFrame({
        'values': [1, 2, 3, 4, 5, 100]  # 100 is an outlier
    })
    
    outliers = detect_outliers_iqr(df, 'values')
    
    assert outliers.iloc[5] == True  # 100 should be detected
    assert outliers.iloc[0] == False  # 1 should not be detected

def test_filter_outliers():
    """Test filtering of outliers."""
    df = pd.DataFrame({
        'values': [1, 2, 3, 4, 5, 100],
        'other': [1, 1, 1, 1, 1, 1]
    })
    
    filtered = filter_outliers(df, ['values'])
    
    assert len(filtered) == 5  # One outlier removed
    assert 100 not in filtered['values'].values

def test_calculate_checksum():
    """Test checksum calculation."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test content")
        temp_path = f.name
    
    try:
        checksum = calculate_checksum(temp_path)
        assert len(checksum) == 64  # SHA-256 hex length
    finally:
        os.unlink(temp_path)

def test_register_checksum_in_state():
    """Test checksum registration in state file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.parquet') as f:
        f.write("fake parquet content")
        temp_path = f.name
    
    state_path = "state/projects/test_project.yaml"
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(state_path), exist_ok=True)
        
        register_checksum_in_state(temp_path, state_path)
        
        # Verify state file was created and contains checksum
        assert os.path.exists(state_path)
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f)
        
        assert 'artifact_hashes' in state
        # Check that the file is in the hashes (key might be relative path)
        assert len(state['artifact_hashes']) > 0
    finally:
        os.unlink(temp_path)
        if os.path.exists(state_path):
            os.unlink(state_path)
        # Clean up test directory if empty
        test_dir = "state/projects"
        if os.path.exists(test_dir) and not os.listdir(test_dir):
            os.rmdir(test_dir)
        if os.path.exists("state") and not os.listdir("state"):
            os.rmdir("state")
