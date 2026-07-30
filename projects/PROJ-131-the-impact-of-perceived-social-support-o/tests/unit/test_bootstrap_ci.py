import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os
import yaml

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.bootstrap_ci import load_seed_config, compute_bca_bootstrap_ci, run_bootstrap_analysis

@pytest.fixture
def sample_data():
    """Create a small synthetic dataset for testing the bootstrap logic."""
    np.random.seed(42)
    n = 200
    data = {
        'social_support': np.random.normal(50, 10, n),
        'harassment_severity': np.random.normal(3, 1, n),
        'age': np.random.normal(30, 5, n),
        'gender': np.random.choice([0, 1], n),
        'education': np.random.choice([1, 2, 3, 4], n),
        'income': np.random.normal(50000, 10000, n),
        'depression': np.random.normal(15, 5, n),
        'anxiety': np.random.normal(10, 4, n)
    }
    # Create interaction term explicitly to ensure it's in the formula
    # But we rely on the formula string to create it.
    return pd.DataFrame(data)

@pytest.fixture
def temp_seed_file(tmp_path):
    """Create a temporary seed config file."""
    seed_file = tmp_path / "seeds.yaml"
    seed_file.write_text("random_seed: 12345")
    return str(seed_file)

def test_load_seed_config_success(temp_seed_file):
    seed = load_seed_config(temp_seed_file)
    assert seed == 12345

def test_load_seed_config_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_seed_config(str(tmp_path / "nonexistent.yaml"))

def test_load_seed_config_missing_key(tmp_path):
    seed_file = tmp_path / "seeds.yaml"
    seed_file.write_text("other_key: 123")
    with pytest.raises(ValueError):
        load_seed_config(str(seed_file))

def test_compute_bca_bootstrap_ci_basic(sample_data):
    """Test that the function returns a valid dictionary with expected keys."""
    # Use a small number of resamples for speed in unit tests
    result = compute_bca_bootstrap_ci(
        df=sample_data,
        formula='depression ~ social_support * harassment_severity + age + gender',
        outcome_col='depression',
        predictor_col='social_support',
        interaction_col='social_support:harassment_severity',
        n_resamples=10, # Small number for unit test speed
        seed=42
    )
    
    assert isinstance(result, dict)
    required_keys = ['coef', 'se', 'pvalue', 'ci_lower', 'ci_upper', 'n_resamples']
    for key in required_keys:
        assert key in result
    
    # Check types
    assert isinstance(result['coef'], (int, float, np.floating))
    assert isinstance(result['ci_lower'], (int, float, np.floating))
    assert isinstance(result['ci_upper'], (int, float, np.floating))
    assert result['n_resamples'] == 10

def test_compute_bca_bootstrap_ci_ci_order(sample_data):
    """Test that the lower CI is less than the upper CI."""
    result = compute_bca_bootstrap_ci(
        df=sample_data,
        formula='depression ~ social_support * harassment_severity + age + gender',
        outcome_col='depression',
        predictor_col='social_support',
        interaction_col='social_support:harassment_severity',
        n_resamples=10,
        seed=42
    )
    assert result['ci_lower'] <= result['ci_upper']

def test_run_bootstrap_analysis(sample_data):
    """Test the multi-outcome bootstrap function."""
    formulas = {
        'depression': 'depression ~ social_support * harassment_severity + age + gender',
        'anxiety': 'anxiety ~ social_support * harassment_severity + age + gender'
    }
    
    results_df = run_bootstrap_analysis(
        df=sample_data,
        formulas=formulas,
        interaction_col='social_support:harassment_severity',
        n_resamples=10,
        seed=42
    )
    
    assert isinstance(results_df, pd.DataFrame)
    assert 'outcome' in results_df.columns
    assert len(results_df) == 2
    assert set(results_df['outcome'].tolist()) == {'depression', 'anxiety'}
    
    # Check for NaNs if something went wrong (though with seed 42 and small n it should work)
    # We just check the structure is correct.
    assert 'coef' in results_df.columns
    assert 'ci_lower' in results_df.columns
    assert 'ci_upper' in results_df.columns

def test_interaction_term_missing(sample_data):
    """Test that the function raises an error if interaction term is not in model."""
    with pytest.raises(ValueError):
        compute_bca_bootstrap_ci(
            df=sample_data,
            formula='depression ~ social_support + harassment_severity', # No interaction
            outcome_col='depression',
            predictor_col='social_support',
            interaction_col='social_support:harassment_severity',
            n_resamples=10,
            seed=42
        )
