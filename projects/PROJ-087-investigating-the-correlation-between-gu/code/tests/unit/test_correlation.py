import pytest
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from src.correlation import (
    calculate_spearman_correlation,
    apply_benjamini_hochberg,
    flag_correlations,
    handle_no_significant_associations,
    run_correlation_analysis
)

@pytest.fixture
def sample_diversity_df():
    """Create a sample DataFrame for testing correlation functions."""
    np.random.seed(42)
    n_samples = 100
    return pd.DataFrame({
        'sample_id': range(n_samples),
        'shannon': np.random.normal(3.5, 0.5, n_samples),
        'simpson': np.random.normal(0.85, 0.05, n_samples),
        'observed_otus': np.random.normal(150, 20, n_samples),
        'sleep_efficiency': np.random.normal(85, 10, n_samples),
        'sleep_duration_hours': np.random.normal(7.5, 1, n_samples),
        'antibiotic_use_last_3m': [False] * n_samples
    })

def test_spearman_correlation_calculation(sample_diversity_df):
    """Test that Spearman correlation is calculated correctly."""
    sleep_metrics = ['sleep_efficiency']
    diversity_metrics = ['shannon']
    
    result = calculate_spearman_correlation(
        sample_diversity_df, 
        sleep_metrics, 
        diversity_metrics
    )
    
    assert len(result) == 1
    assert 'correlation_coefficient' in result.columns
    assert 'p_value' in result.columns
    assert -1 <= result['correlation_coefficient'].iloc[0] <= 1
    assert 0 <= result['p_value'].iloc[0] <= 1

def test_benjamini_hochberg_correction(sample_diversity_df):
    """Test that Benjamini-Hochberg correction is applied correctly."""
    # Create a known set of p-values
    df = pd.DataFrame({
        'p_value': [0.01, 0.02, 0.03, 0.04, 0.05, 0.10, 0.20, 0.50]
    })
    
    result = apply_benjamini_hochberg(df, alpha=0.05)
    
    assert 'q_value' in result.columns
    assert 'is_significant' in result.columns
    assert len(result) == 8
    
    # Q-values should be monotonically increasing when sorted by p-value
    sorted_q = result.sort_values('p_value')['q_value'].values
    assert all(sorted_q[i] <= sorted_q[i+1] for i in range(len(sorted_q)-1))
    
    # All q-values should be <= 1
    assert all(result['q_value'] <= 1.0)

def test_flag_correlations(sample_diversity_df):
    """Test that correlation flags are set correctly."""
    df = pd.DataFrame({
        'sleep_metric': ['A', 'B', 'C'],
        'diversity_metric': ['X', 'Y', 'Z'],
        'correlation_coefficient': [0.5, -0.2, 0.1],
        'p_value': [0.01, 0.03, 0.04],
        'q_value': [0.02, 0.05, 0.06],
        'is_significant': [True, True, False]
    })
    
    result = flag_correlations(df, r_threshold=0.3)
    
    assert 'is_moderate' in result.columns
    assert 'is_meaningful' in result.columns
    assert 'significance' in result.columns
    
    # Check flags
    assert result.iloc[0]['is_moderate'] is True   # |0.5| > 0.3
    assert result.iloc[1]['is_moderate'] is False  # |-0.2| < 0.3
    assert result.iloc[2]['is_moderate'] is False  # |0.1| < 0.3
    
    # Meaningful requires both significant and moderate
    assert result.iloc[0]['is_meaningful'] is True
    assert result.iloc[1]['is_meaningful'] is False
    assert result.iloc[2]['is_meaningful'] is False

def test_empty_dataframe_handling(sample_diversity_df):
    """Test handling of empty DataFrames."""
    empty_df = pd.DataFrame(columns=['sleep_metric', 'diversity_metric', 'p_value'])
    
    result = apply_benjamini_hochberg(empty_df)
    assert len(result) == 0
    assert 'q_value' in result.columns
    assert 'is_significant' in result.columns

def test_handle_no_significant_associations(sample_diversity_df):
    """Test the function that checks for significant associations."""
    # DataFrame with no significant results
    df_no_sig = pd.DataFrame({
        'is_significant': [False, False, False]
    })
    assert handle_no_significant_associations(df_no_sig) is True
    
    # DataFrame with some significant results
    df_some_sig = pd.DataFrame({
        'is_significant': [True, False, False]
    })
    assert handle_no_significant_associations(df_some_sig) is False
    
    # Empty DataFrame
    df_empty = pd.DataFrame(columns=['is_significant'])
    assert handle_no_significant_associations(df_empty) is True
