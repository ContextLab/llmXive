import pytest
import pandas as pd
import numpy as np
from code.analysis import run_inverse_probability_weighting, run_complete_case_analysis, run_multiple_imputation

@pytest.fixture
def sample_data_missing():
    """Create a sample dataframe with missing values."""
    np.random.seed(42)
    n = 100
    data = {
        'outcome': np.random.normal(loc=0, scale=1, size=n),
        'treatment': np.random.choice([0, 1], size=n),
        'covariate': np.random.normal(loc=0, scale=1, size=n)
    }
    df = pd.DataFrame(data)
    # Introduce missingness dependent on covariate (MAR)
    # Higher covariate -> more likely to be missing
    missing_prob = 1 / (1 + np.exp(-df['covariate']))
    mask = np.random.random(n) < missing_prob
    df.loc[mask, 'outcome'] = np.nan
    return df

def test_run_inverse_probability_weighting_mar(sample_data_missing):
    """Test IPW with MAR data."""
    result = run_inverse_probability_weighting(
        sample_data_missing, 
        outcome_col='outcome', 
        treatment_col='treatment'
    )
    assert 'p_value' in result
    assert 'statistic' in result
    assert result['method'] == 'ipw'
    assert isinstance(result['p_value'], float)
    assert 0.0 <= result['p_value'] <= 1.0

def test_run_inverse_probability_weighting_no_covariates():
    """Test IPW with no covariates (MCAR assumption)."""
    np.random.seed(42)
    n = 100
    data = {
        'outcome': np.random.normal(loc=0, scale=1, size=n),
        'treatment': np.random.choice([0, 1], size=n)
    }
    df = pd.DataFrame(data)
    # Random missingness
    mask = np.random.random(n) < 0.3
    df.loc[mask, 'outcome'] = np.nan
    
    result = run_inverse_probability_weighting(
        df, 
        outcome_col='outcome', 
        treatment_col='treatment'
    )
    assert 'p_value' in result
    assert result['method'] == 'ipw'

def test_run_inverse_probability_weighting_all_missing():
    """Test IPW when all outcomes are missing."""
    df = pd.DataFrame({
        'outcome': [np.nan] * 50,
        'treatment': [0, 1] * 25
    })
    with pytest.raises(ValueError, match="No observed outcomes found"):
        run_inverse_probability_weighting(df, 'outcome', 'treatment')

def test_run_inverse_probability_weighting_binary_outcome(sample_data_missing):
    """Test IPW with binary outcome."""
    df = sample_data_missing.copy()
    df['outcome'] = (df['outcome'] > df['outcome'].median()).astype(int)
    
    result = run_inverse_probability_weighting(
        df, 
        outcome_col='outcome', 
        treatment_col='treatment'
    )
    assert 'p_value' in result
    assert result['method'] == 'ipw'