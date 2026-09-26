import pytest
import pandas as pd
import numpy as np
from code.analysis import calculate_partial_spearman_alpha

def test_partial_spearman_with_covariates():
    """Test that partial Spearman adjusts for covariates correctly."""
    # Create mock data
    np.random.seed(42)
    n = 100
    
    # Create covariates
    age = np.random.normal(50, 10, n)
    bmi = np.random.normal(25, 4, n)
    
    # Create true relationship: diversity increases with age, PHQ decreases with age
    # But no direct relationship between diversity and PHQ
    diversity = age * 0.5 + np.random.normal(0, 1, n)
    phq = -age * 0.5 + np.random.normal(0, 1, n)
    
    alpha_df = pd.DataFrame({
        'sample_id': [f's{i}' for i in range(n)],
        'shannon': diversity
    })
    
    mh_df = pd.DataFrame({
        'sample_id': [f's{i}' for i in range(n)],
        'phq9': phq,
        'age': age,
        'bmi': bmi
    })
    
    # Without adjustment, there should be a correlation due to confounding
    # With adjustment, correlation should be near zero
    results = calculate_partial_spearman_alpha(
        alpha_df, 
        mh_df, 
        covariates=['age', 'bmi']
    )
    
    # Check that we got results
    assert len(results['coefficients']) > 0
    assert results['n_samples'] == n
    
    # The partial correlation should be much lower than the raw correlation
    # (raw correlation exists because both depend on age)
    raw_corr = np.corrcoef(diversity, phq)[0, 1]
    partial_corr = results['coefficients'].get('shannon_phq9', 0)
    
    # Assert that partial correlation is significantly closer to 0 than raw
    # (This is a soft check; exact values depend on random noise)
    assert abs(partial_corr) < abs(raw_corr), \
        f"Partial corr ({partial_corr}) should be closer to 0 than raw ({raw_corr})"

def test_partial_spearman_no_covariates():
    """Test that function works when no covariates are provided."""
    np.random.seed(42)
    n = 50
    
    alpha_df = pd.DataFrame({
        'sample_id': [f's{i}' for i in range(n)],
        'shannon': np.random.normal(0, 1, n)
    })
    
    mh_df = pd.DataFrame({
        'sample_id': [f's{i}' for i in range(n)],
        'phq9': np.random.normal(0, 1, n)
    })
    
    results = calculate_partial_spearman_alpha(alpha_df, mh_df, covariates=[])
    
    assert len(results['coefficients']) > 0
    assert results['n_samples'] == n
    assert results['covariates_used'] == []

def test_partial_spearman_missing_data():
    """Test handling of missing values."""
    np.random.seed(42)
    n = 50
    
    alpha_df = pd.DataFrame({
        'sample_id': [f's{i}' for i in range(n)],
        'shannon': np.random.normal(0, 1, n)
    })
    
    mh_df = pd.DataFrame({
        'sample_id': [f's{i}' for i in range(n)],
        'phq9': np.random.normal(0, 1, n)
    })
    
    # Introduce missing values
    alpha_df.loc[0, 'shannon'] = np.nan
    mh_df.loc[1, 'phq9'] = np.nan
    
    results = calculate_partial_spearman_alpha(alpha_df, mh_df)
    
    # Should have fewer samples due to missing data
    assert results['n_samples'] < n
    assert len(results['coefficients']) > 0