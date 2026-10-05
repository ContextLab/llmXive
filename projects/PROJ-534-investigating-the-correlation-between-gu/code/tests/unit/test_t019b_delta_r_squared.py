import pytest
import pandas as pd
import numpy as np
from code.src.analysis.correlation import run_multiple_regressions

def test_baseline_and_full_model():
    """Test that baseline and full models are calculated correctly."""
    # Create synthetic data
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        'cognitive_flexibility_score': np.random.normal(50, 10, n),
        'shannon_diversity': np.random.normal(3.5, 0.5, n),
        'age': np.random.normal(70, 5, n),
        'sex': np.random.choice([0, 1], n),
        'bmi': np.random.normal(25, 3, n),
        'dietary_fiber_intake': np.random.normal(25, 5, n),
        'antibiotic_use_history': np.random.choice([0, 1], n)
    })
    
    covariates = ['age', 'sex', 'bmi', 'dietary_fiber_intake', 'antibiotic_use_history']
    dependent_var = 'cognitive_flexibility_score'
    diversity_var = 'shannon_diversity'
    
    results = run_multiple_regressions(df, dependent_var, diversity_var, covariates)
    
    # Check that both models have results
    assert 'baseline_model' in results
    assert 'full_model' in results
    assert 'delta_r_squared' in results
    
    # Check that R-squared values are numeric
    assert isinstance(results['baseline_model']['r_squared'], (int, float))
    assert isinstance(results['full_model']['r_squared'], (int, float))
    
    # Check that delta R-squared is calculated
    expected_delta = results['full_model']['r_squared'] - results['baseline_model']['r_squared']
    assert np.isclose(results['delta_r_squared'], expected_delta, rtol=1e-5)
    
    # Check that coefficients and p-values are present
    assert 'coefficients' in results['baseline_model']
    assert 'p_values' in results['baseline_model']
    assert 'coefficients' in results['full_model']
    assert 'p_values' in results['full_model']

def test_delta_r_squared_with_nan():
    """Test that delta R-squared is NaN when inputs are NaN."""
    df = pd.DataFrame({
        'cognitive_flexibility_score': [np.nan, np.nan, np.nan],
        'shannon_diversity': [np.nan, np.nan, np.nan],
        'age': [np.nan, np.nan, np.nan],
        'sex': [np.nan, np.nan, np.nan],
        'bmi': [np.nan, np.nan, np.nan],
        'dietary_fiber_intake': [np.nan, np.nan, np.nan],
        'antibiotic_use_history': [np.nan, np.nan, np.nan]
    })
    
    covariates = ['age', 'sex', 'bmi', 'dietary_fiber_intake', 'antibiotic_use_history']
    dependent_var = 'cognitive_flexibility_score'
    diversity_var = 'shannon_diversity'
    
    results = run_multiple_regressions(df, dependent_var, diversity_var, covariates)
    
    assert np.isnan(results['baseline_model']['r_squared'])
    assert np.isnan(results['full_model']['r_squared'])
    assert results['delta_r_squared'] is None

def test_delta_r_squared_positive():
    """Test that adding a predictor can increase R-squared."""
    np.random.seed(42)
    n = 100
    # Create data where diversity has a strong effect
    base_score = np.random.normal(50, 5, n)
    diversity_effect = np.random.normal(0, 0.1, n)
    df = pd.DataFrame({
        'cognitive_flexibility_score': base_score + diversity_effect * 10,
        'shannon_diversity': np.random.normal(3.5, 0.5, n),
        'age': np.random.normal(70, 5, n),
        'sex': np.random.choice([0, 1], n),
        'bmi': np.random.normal(25, 3, n),
        'dietary_fiber_intake': np.random.normal(25, 5, n),
        'antibiotic_use_history': np.random.choice([0, 1], n)
    })
    
    covariates = ['age', 'sex', 'bmi', 'dietary_fiber_intake', 'antibiotic_use_history']
    dependent_var = 'cognitive_flexibility_score'
    diversity_var = 'shannon_diversity'
    
    results = run_multiple_regressions(df, dependent_var, diversity_var, covariates)
    
    # Full model should have higher R-squared than baseline
    assert results['full_model']['r_squared'] >= results['baseline_model']['r_squared']
    assert results['delta_r_squared'] >= 0