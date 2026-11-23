"""
Unit tests for T027: Tobit Regression with Fallback.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import os

# Import the functions to test
from code.analysis_tobit import (
    load_retrieval_data,
    calculate_vif,
    prepare_tobit_data,
    fit_tobit_model_and_save,
    run_ridge_fallback
)

@pytest.fixture
def sample_data():
    """Create a mock dataset for testing."""
    data = {
        'planet_name': [f'planet_{i}' for i in range(10)],
        'water_mixing_ratio': np.random.uniform(-5, -2, 10),
        'is_upper_limit': [False] * 10,
        'temperature': np.random.uniform(1000, 2000, 10),
        'mass': np.random.uniform(1, 10, 10),
        'metallicity': np.random.uniform(-0.5, 0.5, 10)
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_csv(sample_data):
    """Create a temporary CSV file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        sample_data.to_csv(f.name, index=False)
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def temp_json():
    """Create a temporary JSON file path."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
        yield f.name
    os.unlink(f.name)

def test_load_retrieval_data(temp_csv):
    """Test loading data from CSV."""
    df = load_retrieval_data(temp_csv)
    assert len(df) == 10
    assert 'water_mixing_ratio' in df.columns
    assert 'metallicity' in df.columns

def test_calculate_vif(sample_data):
    """Test VIF calculation."""
    features = ['temperature', 'mass', 'metallicity']
    vif = calculate_vif(sample_data, features)
    assert len(vif) == 3
    assert all(isinstance(v, float) for v in vif.values())

def test_prepare_tobit_data(sample_data):
    """Test data preparation."""
    y, X, names = prepare_tobit_data(sample_data)
    assert len(y) == 10
    assert X.shape == (10, 3)
    assert len(names) == 3

def test_run_ridge_fallback(sample_data):
    """Test Ridge fallback."""
    y, X, _ = prepare_tobit_data(sample_data)
    result = run_ridge_fallback(y, X)
    assert result['success'] is True
    assert result['model_type'] == 'Ridge (L2 Penalized) Fallback'
    assert 'coefficients' in result

def test_fit_tobit_model_and_save(temp_csv, temp_json):
    """Test the full pipeline."""
    result = fit_tobit_model_and_save(temp_csv, temp_json)
    
    assert 'vif_check' in result
    assert 'fallback_triggered' in result
    assert 'coefficients' in result
    
    # Verify file was written
    assert Path(temp_json).exists()
    with open(temp_json, 'r') as f:
        saved_data = json.load(f)
    assert saved_data['vif_check'] == result['vif_check']