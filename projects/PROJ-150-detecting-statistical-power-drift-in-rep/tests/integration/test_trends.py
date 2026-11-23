import os
import sys
import pickle
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from compute_trends import load_and_prepare_data, fit_mixed_linear_model, extract_year_statistics, save_results, save_summary

@pytest.fixture
def sample_power_data(tmp_path):
    """Create a sample power_estimates.csv for testing."""
    data = {
        'study_id': ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8'],
        'year': [2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007],
        'field': ['Psych', 'Psych', 'Phys', 'Phys', 'Psych', 'Phys', 'Psych', 'Phys'],
        'original_study_id': ['id1', 'id1', 'id2', 'id2', 'id1', 'id2', 'id1', 'id2'],
        'effect_size': [0.5, 0.6, 0.4, 0.3, 0.7, 0.5, 0.8, 0.2],
        'sample_size': [50, 60, 40, 30, 70, 50, 80, 20],
        'power_est': [0.4, 0.5, 0.3, 0.2, 0.6, 0.4, 0.7, 0.1]
    }
    df = pd.DataFrame(data)
    file_path = tmp_path / "power_estimates.csv"
    df.to_csv(file_path, index=False)
    return file_path

def test_load_and_prepare_data(sample_power_data, tmp_path):
    """Test data loading and preparation."""
    df = load_and_prepare_data(str(sample_power_data))
    assert len(df) > 0
    assert 'power_est' in df.columns
    assert 'year' in df.columns
    assert df['field'].dtype.name == 'category'
    assert df['original_study_id'].dtype.name == 'category'

def test_fit_mixed_linear_model(sample_power_data, tmp_path):
    """Test fitting the LMM model."""
    df = load_and_prepare_data(str(sample_power_data))
    results = fit_mixed_linear_model(df)
    assert results is not None
    assert hasattr(results, 'params')
    # Check that 'year' is in the params
    assert 'year' in results.params.index

def test_extract_year_statistics(sample_power_data, tmp_path):
    """Test extracting year statistics from the model."""
    df = load_and_prepare_data(str(sample_power_data))
    results = fit_mixed_linear_model(df)
    stats = extract_year_statistics(results)
    assert 'slope_year' in stats
    assert 'se_year' in stats
    assert 'p_value' in stats
    assert isinstance(stats['slope_year'], (int, float, np.floating))
    assert isinstance(stats['p_value'], (int, float, np.floating))

def test_save_results(sample_power_data, tmp_path):
    """Test saving model results."""
    df = load_and_prepare_data(str(sample_power_data))
    results = fit_mixed_linear_model(df)
    model_path = tmp_path / "model.pkl"
    raw_path = tmp_path / "raw.pkl"
    save_results(results, str(model_path), str(raw_path))
    assert os.path.exists(model_path)
    assert os.path.exists(raw_path)
    
    # Verify we can load it back
    with open(model_path, 'rb') as f:
        loaded_model = pickle.load(f)
    assert loaded_model is not None

def test_save_summary(sample_power_data, tmp_path):
    """Test saving summary statistics."""
    df = load_and_prepare_data(str(sample_power_data))
    results = fit_mixed_linear_model(df)
    stats = extract_year_statistics(results)
    summary_path = tmp_path / "summary.csv"
    save_summary(stats, str(summary_path))
    assert os.path.exists(summary_path)
    df_summary = pd.read_csv(summary_path)
    assert 'slope_year' in df_summary.columns
    assert 'p_value' in df_summary.columns

def test_full_pipeline(sample_power_data, tmp_path):
    """Test the full pipeline from data to summary."""
    # This simulates the main function logic
    model_path = tmp_path / "model.pkl"
    raw_path = tmp_path / "raw.pkl"
    summary_path = tmp_path / "summary.csv"

    df = load_and_prepare_data(str(sample_power_data))
    results = fit_mixed_linear_model(df)
    stats = extract_year_statistics(results)
    save_results(results, str(model_path), str(raw_path))
    save_summary(stats, str(summary_path))

    # Verify all files exist
    assert os.path.exists(model_path)
    assert os.path.exists(raw_path)
    assert os.path.exists(summary_path)

    # Verify model has random effects structure (simulated by checking params)
    with open(model_path, 'rb') as f:
        loaded_model = pickle.load(f)
    assert 'year' in loaded_model.params.index