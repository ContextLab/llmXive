"""
Integration tests for compute_trends.py
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pickle
import pandas as pd
import numpy as np
import pytest

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from compute_trends import load_and_prepare_data, fit_mixed_linear_model, save_results

@pytest.fixture
def sample_data():
    """Create a minimal synthetic dataset for testing the pipeline logic."""
    np.random.seed(42)
    n = 100
    data = {
        'year': np.random.randint(1980, 2020, n),
        'effect_size': np.random.normal(0.3, 0.1, n),
        'sample_size': np.random.randint(20, 100, n),
        'field': np.random.choice(['Psychology', 'Biology', 'Physics'], n),
        'original_study_id': [f"study_{i}" for i in range(n)]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp)

def test_load_and_prepare_data(sample_data, temp_dir):
    """Test data loading and cleaning."""
    csv_path = temp_dir / "data.csv"
    sample_data.to_csv(csv_path, index=False)

    df = load_and_prepare_data(csv_path)

    assert 'power_est' in df.columns
    assert len(df) > 0
    assert all(df['power_est'] >= 0)
    assert all(df['power_est'] <= 1)

def test_fit_mixed_linear_model(sample_data, temp_dir):
    """Test LMM fitting."""
    csv_path = temp_dir / "data.csv"
    sample_data.to_csv(csv_path, index=False)
    df = load_and_prepare_data(csv_path)

    # Ensure enough groups for random effects
    # The fixture creates unique study IDs, so n_groups = 100.
    result = fit_mixed_linear_model(df)

    assert result is not None
    assert hasattr(result, 'feffects')
    assert 'year' in result.feffects.index
    assert result.converged

def test_save_results(sample_data, temp_dir):
    """Test saving model results."""
    csv_path = temp_dir / "data.csv"
    sample_data.to_csv(csv_path, index=False)
    df = load_and_prepare_data(csv_path)
    result = fit_mixed_linear_model(df)
    
    output_dir = temp_dir / "output"
    save_results(result, df, output_dir)

    model_path = output_dir / "input_trends_models.pkl"
    params_path = output_dir / "input_trends_raw.pkl"

    assert model_path.exists()
    assert params_path.exists()

    with open(model_path, 'rb') as f:
        loaded_model = pickle.load(f)
    assert loaded_model is not None
    assert hasattr(loaded_model, 'feffects')

    with open(params_path, 'rb') as f:
        loaded_params = pickle.load(f)
    assert 'fixed_effects' in loaded_params
    assert 'random_effects' in loaded_params
    assert 'year' in loaded_params['fixed_effects'].index