"""
Unit tests for generate_regression_summary.py
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from generate_regression_summary import calculate_vif, generate_summary_dataframe, load_regression_results
from config import get_project_root

@pytest.fixture
def sample_user_track_data():
    """Create sample user-track data for VIF testing."""
    np.random.seed(42)
    n = 100
    data = {
        'user_id': np.random.choice(['A', 'B', 'C'], n),
        'track_id': np.random.choice([1, 2, 3, 4, 5], n),
        'residualized_exposure': np.random.normal(0, 1, n),
        'popularity': np.random.normal(50, 20, n),
        'mean_vividness': np.random.normal(5, 1, n),
        'mean_valence': np.random.normal(0, 1, n)
    }
    # Add some correlation between predictors to test VIF
    data['popularity'] = data['popularity'] + 0.3 * data['residualized_exposure']
    return pd.DataFrame(data)

@pytest.fixture
def sample_regression_results():
    """Create sample regression results."""
    return pd.DataFrame([
        {'model_name': 'vividness_model', 'term': 'Intercept', 'estimate': 4.5, 'std_err': 0.2, 'pvalue': 0.001, 'model_type': 'fixed', 'formula': 'mean_vividness ~ residualized_exposure + popularity'},
        {'model_name': 'vividness_model', 'term': 'residualized_exposure', 'estimate': 0.3, 'std_err': 0.05, 'pvalue': 0.003, 'model_type': 'fixed', 'formula': 'mean_vividness ~ residualized_exposure + popularity'},
        {'model_name': 'vividness_model', 'term': 'popularity', 'estimate': 0.02, 'std_err': 0.008, 'pvalue': 0.012, 'model_type': 'fixed', 'formula': 'mean_vividness ~ residualized_exposure + popularity'},
        {'model_name': 'valence_model', 'term': 'Intercept', 'estimate': 0.1, 'std_err': 0.15, 'pvalue': 0.50, 'model_type': 'fixed', 'formula': 'mean_valence ~ residualized_exposure + popularity'},
        {'model_name': 'valence_model', 'term': 'residualized_exposure', 'estimate': 0.05, 'std_err': 0.04, 'pvalue': 0.20, 'model_type': 'fixed', 'formula': 'mean_valence ~ residualized_exposure + popularity'},
        {'model_name': 'valence_model', 'term': 'popularity', 'estimate': -0.01, 'std_err': 0.005, 'pvalue': 0.04, 'model_type': 'fixed', 'formula': 'mean_valence ~ residualized_exposure + popularity'}
    ])

def test_calculate_vif_basic(sample_user_track_data):
    """Test VIF calculation with basic formula."""
    formula = 'mean_vividness ~ residualized_exposure + popularity'
    vif_df = calculate_vif(sample_user_track_data, formula)
    
    assert isinstance(vif_df, pd.DataFrame)
    assert 'term' in vif_df.columns
    assert 'vif' in vif_df.columns
    assert len(vif_df) == 2  # Two predictors
    assert all(vif_df['vif'] >= 1.0)  # VIF is always >= 1

def test_calculate_vif_invalid_formula(sample_user_track_data):
    """Test VIF calculation with invalid formula."""
    vif_df = calculate_vif(sample_user_track_data, 'invalid_formula')
    assert len(vif_df) == 0

def test_calculate_vif_no_predictors(sample_user_track_data):
    """Test VIF calculation with no predictors."""
    vif_df = calculate_vif(sample_user_track_data, 'mean_vividness ~ 1')
    assert len(vif_df) == 0

def test_generate_summary_dataframe(sample_regression_results, sample_user_track_data):
    """Test summary dataframe generation."""
    summary_df = generate_summary_dataframe(sample_regression_results, sample_user_track_data)
    
    assert isinstance(summary_df, pd.DataFrame)
    assert not summary_df.empty
    assert 'model' in summary_df.columns
    assert 'term' in summary_df.columns
    assert 'estimate' in summary_df.columns
    assert 'std_err' in summary_df.columns
    assert 'pvalue' in summary_df.columns
    assert 'vif' in summary_df.columns
    assert 'significance' in summary_df.columns
    
    # Check that we have entries for both models
    assert 'vividness_model' in summary_df['model'].values
    assert 'valence_model' in summary_df['model'].values

def test_generate_summary_dataframe_empty_input():
    """Test summary generation with empty inputs."""
    empty_results = pd.DataFrame()
    empty_data = pd.DataFrame()
    
    summary_df = generate_summary_dataframe(empty_results, empty_data)
    assert summary_df.empty

def test_significance_stars(sample_regression_results, sample_user_track_data):
    """Test that significance stars are correctly assigned."""
    summary_df = generate_summary_dataframe(sample_regression_results, sample_user_track_data)
    
    # Check that significance column exists and has expected values
    assert all(summary_df['significance'].isin(['ns', '*', '**', '***']))
    
    # Check specific cases
    vividness_rows = summary_df[summary_df['model'] == 'vividness_model']
    # Intercept p=0.001 -> ***
    intercept_row = vividness_rows[vividness_rows['term'] == 'Intercept']
    if not intercept_row.empty:
        assert intercept_row.iloc[0]['significance'] == '***'