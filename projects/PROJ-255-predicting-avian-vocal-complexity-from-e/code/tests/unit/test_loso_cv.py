import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add code directory to path if running from root
code_root = Path(__file__).parent.parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.analysis.modeling import run_loso_cross_validation

@pytest.fixture
def sample_loso_data():
    """
    Generate a synthetic dataset mimicking the structure of final_dataset.csv
    for testing LOSO logic without real audio processing.
    """
    np.random.seed(42)
    n_species = 10
    n_per_species = 20
    
    data = []
    for i in range(n_species):
        species_id = f"species_{i}"
        # True intercept varies by species
        intercept = np.random.normal(0, 2)
        for j in range(n_per_species):
            noise = np.random.uniform(30, 70)
            # Complexity = intercept + 0.5 * noise + noise
            complexity = intercept + 0.5 * noise + np.random.normal(0, 2)
            data.append({
                'species_id': species_id,
                'noise_level_db': noise,
                'complexity_score': complexity,
                'location': f"loc_{i % 3}"
            })
    
    df = pd.DataFrame(data)
    return df

class TestLOSO:
    def test_loso_runs_without_error(self, sample_loso_data):
        """Test that LOSO runs and returns a result dictionary."""
        result = run_loso_cross_validation(sample_loso_data)
        
        assert isinstance(result, dict)
        assert 'cv_results' in result
        assert 'mean_r_squared' in result
        assert 'std_r_squared' in result
        assert 'mean_rmse' in result
        assert 'n_folds' in result
        
        # Check that we have results for each species (minus potential failures)
        assert result['n_folds'] > 0
        assert len(result['cv_results']) > 0

    def test_loso_results_structure(self, sample_loso_data):
        """Test the structure of individual CV results."""
        result = run_loso_cross_validation(sample_loso_data)
        
        for fold_res in result['cv_results']:
            assert 'species' in fold_res
            assert 'r_squared' in fold_res
            assert 'rmse' in fold_res
            assert 'n_test' in fold_res
            
            # R^2 can be negative, but should be a float
            assert isinstance(fold_res['r_squared'], float)
            assert isinstance(fold_res['rmse'], float)
            assert fold_res['n_test'] > 0

    def test_loso_with_missing_columns(self, sample_loso_data):
        """Test that LOSO raises error if required columns are missing."""
        df_wrong = sample_loso_data.rename(columns={'complexity_score': 'wrong_col'})
        
        with pytest.raises(ValueError):
            run_loso_cross_validation(df_wrong)

    def test_loso_aggregates_metrics(self, sample_loso_data):
        """Test that mean/std are calculated correctly."""
        result = run_loso_cross_validation(sample_loso_data)
        
        # Manual check
        r2_values = [r['r_squared'] for r in result['cv_results']]
        rmse_values = [r['rmse'] for r in result['cv_results']]
        
        assert np.isclose(result['mean_r_squared'], np.mean(r2_values))
        assert np.isclose(result['mean_rmse'], np.mean(rmse_values))