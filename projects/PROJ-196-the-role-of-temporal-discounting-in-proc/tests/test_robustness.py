"""
Unit tests for code/robustness.py functions.
"""
import pytest
import pandas as pd
import numpy as np
from code.robustness import (
    bootstrap_interaction,
    sensitivity_analysis,
    calculate_instability_ratio
)

@pytest.fixture
def sample_regression_data():
    """Create sample data for robustness tests."""
    np.random.seed(42)
    n = 200
    data = {
        'participant_id': range(1, n + 1),
        'log_k_centered': np.random.normal(0, 1, n),
        'wm_accuracy_centered': np.random.normal(0, 1, n),
        'procrastination_score': np.random.normal(50, 10, n),
        'interaction': np.random.normal(0, 1, n)
    }
    df = pd.DataFrame(data)
    # Add some correlation
    df['procrastination_score'] = (
        2 * df['log_k_centered'] + 
        1.5 * df['wm_accuracy_centered'] + 
        0.8 * df['interaction'] + 
        np.random.normal(0, 5, n)
    )
    return df

def test_bootstrap_interaction(sample_regression_data):
    """Test bootstrap resampling for interaction effect."""
    results = bootstrap_interaction(
        sample_regression_data,
        n_bootstrap=100,
        seed=42
    )
    
    # Check results structure
    assert 'interaction_coefficients' in results
    assert 'ci_lower' in results
    assert 'ci_upper' in results
    
    # Check that we have the expected number of bootstrap samples
    assert len(results['interaction_coefficients']) == 100

def test_sensitivity_analysis(sample_regression_data):
    """Test sensitivity analysis with different thresholds."""
    results = sensitivity_analysis(
        sample_regression_data,
        n_bootstrap=50,  # Reduced for speed in testing
        seed=42
    )
    
    # Check results structure
    assert 'threshold_results' in results
    assert 'instability_ratio' in results
    
    # Check that instability ratio is between 0 and 1
    assert 0 <= results['instability_ratio'] <= 1

def test_calculate_instability_ratio():
    """Test instability ratio calculation."""
    # Create sample p-values
    p_values = [0.01, 0.03, 0.06, 0.08, 0.04, 0.02, 0.07, 0.09, 0.01, 0.03]
    
    ratio = calculate_instability_ratio(p_values)
    
    # Count how many p-values > 0.05
    non_significant = sum(1 for p in p_values if p > 0.05)
    expected_ratio = non_significant / len(p_values)
    
    assert abs(ratio - expected_ratio) < 1e-6
