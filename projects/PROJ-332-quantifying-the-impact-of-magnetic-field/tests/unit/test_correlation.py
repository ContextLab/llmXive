import pytest
import pandas as pd
import numpy as np
from scipy import stats
from code.analysis.correlation import (
    calculate_spearman_correlation,
    bootstrap_confidence_intervals,
    check_multicollinearity,
    stratify_by_mode,
    calculate_power,
    run_correlation_analysis
)

@pytest.fixture
def sample_data():
    """Create a sample DataFrame for testing."""
    np.random.seed(42)
    n = 20
    data = {
        'discharge_id': range(1000, 1000 + n),
        'island_width': np.random.uniform(0.01, 0.1, n),
        'resonant_surface_density': np.random.uniform(0.5, 2.0, n),
        'tau_e': np.random.uniform(0.1, 0.5, n),
        'q_range': np.random.uniform(0.5, 1.5, n),
        'confinement_mode': np.random.choice(['L-mode', 'H-mode'], n)
    }
    return pd.DataFrame(data)

@pytest.fixture
def correlated_data():
    """Create data with known negative correlation."""
    np.random.seed(42)
    n = 30
    x = np.linspace(0, 10, n)
    y = -0.5 * x + np.random.normal(0, 0.5, n)  # Negative correlation
    
    data = {
        'island_width': x,
        'tau_e': y,
        'confinement_mode': ['L-mode'] * n
    }
    return pd.DataFrame(data)

def test_calculate_spearman_correlation(sample_data):
    """Test Spearman correlation calculation."""
    corr, p_val = calculate_spearman_correlation(
        sample_data['island_width'], 
        sample_data['tau_e']
    )
    
    assert not np.isnan(corr)
    assert 0 <= p_val <= 1
    assert -1 <= corr <= 1

def test_calculate_spearman_with_nan():
    """Test correlation handling of NaN values."""
    x = pd.Series([1.0, 2.0, np.nan, 4.0, 5.0])
    y = pd.Series([2.0, 4.0, 6.0, np.nan, 10.0])
    
    corr, p_val = calculate_spearman_correlation(x, y)
    
    assert not np.isnan(corr)
    assert -1 <= corr <= 1

def test_insufficient_data():
    """Test correlation with insufficient data points."""
    x = pd.Series([1.0, 2.0])
    y = pd.Series([3.0, 4.0])
    
    corr, p_val = calculate_spearman_correlation(x, y)
    
    assert np.isnan(corr)
    assert np.isnan(p_val)

def test_bootstrap_confidence_intervals(correlated_data):
    """Test bootstrap confidence interval calculation."""
    median_corr, lower, upper = bootstrap_confidence_intervals(
        correlated_data['island_width'],
        correlated_data['tau_e'],
        n_iterations=100,  # Small number for speed
        seed=42
    )
    
    assert not np.isnan(median_corr)
    assert lower <= median_corr <= upper
    assert -1 <= median_corr <= 1

def test_multicollinearity_check(sample_data):
    """Test multicollinearity detection."""
    # Create data with high correlation
    df = sample_data.copy()
    df['q_range'] = df['resonant_surface_density'] * 0.99 + np.random.normal(0, 0.01, len(df))
    
    is_collinear, corr_val = check_multicollinearity(
        df, 
        'q_range', 
        'resonant_surface_density',
        threshold=0.95
    )
    
    assert is_collinear
    assert corr_val > 0.95

def test_stratification_sufficient_samples(sample_data):
    """Test stratification when sufficient samples exist."""
    # Ensure we have enough samples in each mode
    sample_data.loc[:9, 'confinement_mode'] = 'L-mode'
    sample_data.loc[10:, 'confinement_mode'] = 'H-mode'
    
    results = stratify_by_mode(
        sample_data,
        ['island_width'],
        'tau_e',
        'confinement_mode',
        min_sample_size=3
    )
    
    assert results['stratification_performed']
    assert 'island_width' in results['stratified_correlations']
    assert 'L-mode' in results['stratified_correlations']['island_width']
    assert 'H-mode' in results['stratified_correlations']['island_width']

def test_stratification_insufficient_samples(sample_data):
    """Test global correlation when samples are insufficient."""
    # Only 2 samples in one mode
    sample_data.loc[:1, 'confinement_mode'] = 'L-mode'
    sample_data.loc[2:, 'confinement_mode'] = 'H-mode'
    
    results = stratify_by_mode(
        sample_data,
        ['island_width'],
        'tau_e',
        'confinement_mode',
        min_sample_size=3
    )
    
    assert not results['stratification_performed']
    assert results['warning'] is not None
    assert 'island_width' in results['global_correlations']

def test_power_analysis():
    """Test power calculation."""
    # High power with large sample and strong effect
    power_high = calculate_power(n=100, r=0.8)
    assert power_high > 0.8
    
    # Low power with small sample
    power_low = calculate_power(n=5, r=0.5)
    assert power_low < 0.5

def test_run_correlation_analysis(sample_data):
    """Test full correlation analysis pipeline."""
    results = run_correlation_analysis(
        sample_data,
        topology_vars=['island_width', 'resonant_surface_density'],
        tau_var='tau_e',
        q_range_var='q_range',
        mode_col='confinement_mode'
    )
    
    assert 'multicollinearity' in results
    assert 'stratification' in results
    assert 'bootstrap_cis' in results
    assert 'power_analysis' in results
    assert 'sample_sizes' in results
    
    # Check sample sizes
    assert results['sample_sizes']['total'] == len(sample_data)
    assert results['sample_sizes']['L-mode'] >= 0
    assert results['sample_sizes']['H-mode'] >= 0