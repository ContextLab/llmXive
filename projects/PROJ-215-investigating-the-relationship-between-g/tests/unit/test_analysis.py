import pytest
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from code.analysis import calculate_partial_spearman_taxa, calculate_partial_spearman_alpha
from sklearn.linear_model import LinearRegression

def test_calculate_partial_spearman_alpha():
    """Test partial Spearman correlation for alpha diversity."""
    # Create synthetic data with known relationship
    n = 100
    age = np.random.normal(30, 10, n)
    bmi = np.random.normal(25, 3, n)
    covariates = pd.DataFrame({'age': age, 'bmi': bmi})

    # Create diversity and MH scores correlated with each other but not covariates
    diversity = np.random.normal(3.5, 0.5, n)
    mh_scores = diversity * 2 + np.random.normal(0, 0.1, n) # Strong correlation

    corr, pval = calculate_partial_spearman_alpha(
        pd.Series(diversity),
        pd.Series(mh_scores),
        covariates
    )

    assert not np.isnan(corr), "Correlation should not be NaN"
    assert not np.isnan(pval), "P-value should not be NaN"
    assert abs(corr) > 0.5, "Correlation should be strong given the synthetic data"
    assert pval < 0.05, "P-value should be significant"

def test_calculate_partial_spearman_taxa():
    """Test partial Spearman correlation for taxa abundances."""
    n = 50
    age = np.random.normal(30, 10, n)
    bmi = np.random.normal(25, 3, n)
    covariates = pd.DataFrame({'age': age, 'bmi': bmi})

    # Create taxa data
    taxa_data = {
        'taxon_A': np.random.normal(100, 20, n),
        'taxon_B': np.random.normal(50, 10, n),
        'taxon_C': np.zeros(n) # All zeros, should be handled
    }
    taxa_df = pd.DataFrame(taxa_data)

    # Create MH scores correlated with taxon_A
    mh_scores = taxa_df['taxon_A'] * 0.5 + np.random.normal(0, 5, n)

    results = calculate_partial_spearman_taxa(taxa_df, pd.Series(mh_scores), covariates)

    assert 'taxon' in results.columns
    assert 'correlation' in results.columns
    assert 'p_value' in results.columns
    assert len(results) == 3 # 3 taxa

    # Check taxon_A has significant correlation
    row_a = results[results['taxon'] == 'taxon_A'].iloc[0]
    assert not np.isnan(row_a['correlation'])
    assert row_a['p_value'] < 0.05

    # Check taxon_C (zeros) is handled
    row_c = results[results['taxon'] == 'taxon_C'].iloc[0]
    assert np.isnan(row_c['correlation']) or np.isnan(row_c['p_value'])

def test_partial_spearman_vs_simple():
    """Verify that partial correlation differs from simple correlation when covariates matter."""
    n = 100
    # Create a confounder
    confounder = np.random.normal(0, 1, n)
    
    # Diversity and MH both correlated with confounder, but not each other directly
    diversity = confounder * 2 + np.random.normal(0, 0.5, n)
    mh = confounder * 2 + np.random.normal(0, 0.5, n)
    
    # Simple correlation should be high
    simple_corr, simple_p = spearmanr(diversity, mh)
    assert simple_corr > 0.8, "Simple correlation should be high due to confounding"

    # Partial correlation (controlling for confounder) should be near zero
    covariates = pd.DataFrame({'confounder': confounder})
    partial_corr, partial_p = calculate_partial_spearman_alpha(
        pd.Series(diversity),
        pd.Series(mh),
        covariates
    )

    assert abs(partial_corr) < 0.3, "Partial correlation should be low after removing confounding"
    assert partial_p > 0.05, "Partial correlation should not be significant"
