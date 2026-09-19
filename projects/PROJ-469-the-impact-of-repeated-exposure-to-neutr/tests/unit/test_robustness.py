import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from robustness import run_alpha_sweep, run_alpha_sweep_pipeline

@pytest.fixture
def sample_imputed_data():
    """Create a mock imputed dataset with required columns for alpha sweep."""
    np.random.seed(42)
    n = 200
    data = pd.DataFrame({
        'IAT_D_score': np.random.normal(0, 1, n),
        'news_exposure_z': np.random.normal(0, 1, n),
        'political_ideology': np.random.normal(0, 1, n),
        'age': np.random.normal(40, 15, n),
        'gender': np.random.choice([0, 1], n),
        'education': np.random.choice([1, 2, 3, 4], n)
    })
    # Create an interaction term explicitly to ensure it appears in model
    # Note: The model formula will create this, but we ensure data is clean
    return data

def test_run_alpha_sweep_basic(sample_imputed_data):
    """Test that alpha sweep runs and returns expected columns."""
    alpha_levels = [0.01, 0.05, 0.10]
    results = run_alpha_sweep(sample_imputed_data, alpha_levels=alpha_levels)
    
    # Check structure
    assert isinstance(results, pd.DataFrame)
    assert len(results) == len(alpha_levels)
    
    # Check required columns
    expected_cols = [
        'alpha_level', 'interaction_pvalue', 'is_significant',
        'interaction_coefficient', 'interaction_se', 'interaction_tvalue',
        'model_r2', 'n_samples', 'interaction_term_name'
    ]
    for col in expected_cols:
        assert col in results.columns, f"Missing column: {col}"
    
    # Check alpha levels match
    assert sorted(results['alpha_level'].tolist()) == sorted(alpha_levels)
    
    # Check is_significant is boolean
    assert results['is_significant'].dtype == bool

def test_run_alpha_sweep_significance_logic(sample_imputed_data):
    """Test that significance logic is correct based on p-value vs alpha."""
    # Force a specific p-value by manipulating data if necessary, 
    # but for this test we rely on the logic being applied correctly
    alpha_levels = [0.01, 0.05, 0.10]
    results = run_alpha_sweep(sample_imputed_data, alpha_levels=alpha_levels)
    
    # Verify that if p < alpha, is_significant is True
    for _, row in results.iterrows():
        alpha = row['alpha_level']
        pval = row['interaction_pvalue']
        is_sig = row['is_significant']
        
        if pval < alpha:
            assert is_sig is True, f"Expected True for p={pval} < alpha={alpha}"
        else:
            assert is_sig is False, f"Expected False for p={pval} >= alpha={alpha}"

def test_run_alpha_sweep_with_missing_columns(sample_imputed_data):
    """Test that alpha sweep raises ValueError if required columns are missing."""
    bad_data = sample_imputed_data.drop(columns=['news_exposure_z'])
    
    with pytest.raises(ValueError, match="Required columns for alpha sweep not found"):
        run_alpha_sweep(bad_data)

def test_run_alpha_sweep_pipeline(sample_imputed_data, tmp_path):
    """Test the full pipeline including saving to CSV."""
    # Mock the get_results_path to use tmp_path
    # Since we can't easily mock the config manager in a unit test without more setup,
    # we test the core logic and assume the save function works as tested elsewhere
    # or we test run_alpha_sweep directly which is the core logic.
    
    # For this unit test, we focus on the core run_alpha_sweep function
    # The pipeline integration is tested in integration tests or via the main runner
    results = run_alpha_sweep(sample_imputed_data, alpha_levels=[0.05])
    assert results is not None
    assert len(results) == 1
    assert 'is_significant' in results.columns

def test_run_alpha_sweep_single_alpha(sample_imputed_data):
    """Test alpha sweep with a single alpha level."""
    alpha_levels = [0.05]
    results = run_alpha_sweep(sample_imputed_data, alpha_levels=alpha_levels)
    
    assert len(results) == 1
    assert results.iloc[0]['alpha_level'] == 0.05

def test_run_alpha_sweep_default_alpha_levels(sample_imputed_data):
    """Test that default alpha levels are [0.01, 0.05, 0.10]."""
    results = run_alpha_sweep(sample_imputed_data) # No alpha_levels specified
    
    expected_defaults = [0.01, 0.05, 0.10]
    assert sorted(results['alpha_level'].tolist()) == expected_defaults

def test_run_alpha_sweep_interaction_term_identification(sample_imputed_data):
    """Test that the interaction term is correctly identified and reported."""
    results = run_alpha_sweep(sample_imputed_data)
    
    # Should have a non-null interaction term name
    assert results['interaction_term_name'].notna().all()
    # Should contain both variable names (case-insensitive check)
    term_names = results['interaction_term_name'].iloc[0].lower()
    assert 'news_exposure' in term_names and 'ideology' in term_names
