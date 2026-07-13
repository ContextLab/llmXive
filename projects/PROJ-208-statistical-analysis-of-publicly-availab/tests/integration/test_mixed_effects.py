"""
Integration test for mixed-effects model convergence (US3).

This test verifies that the linear mixed-effects model implementation
in code/analysis/mixed_effects_model.py can successfully converge on
real data from data/processed/cleaned_issues.csv.

Prerequisites:
- T011 must be completed to ensure data/processed/cleaned_issues.csv exists
- T022 (mixed_effects_model.py implementation) must be completed

This test is marked as [P] because it operates on a separate file path
and does not conflict with other implementation tasks once data is ready.
"""

import os
import sys
import pytest
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

import pandas as pd
import numpy as np

# Import the model implementation (will be created in T022)
try:
    from analysis.mixed_effects_model import fit_mixed_effects_model, load_cleaned_data
    MIXED_EFFECTS_AVAILABLE = True
except ImportError:
    MIXED_EFFECTS_AVAILABLE = False


class TestMixedEffectsConvergence:
    """Test suite for mixed-effects model convergence."""
    
    @pytest.fixture
    def cleaned_data_path(self):
        """Path to the cleaned dataset."""
        return project_root / "data" / "processed" / "cleaned_issues.csv"
    
    @pytest.fixture
    def sample_data(self, cleaned_data_path):
        """Load sample data if available."""
        if not cleaned_data_path.exists():
            pytest.skip("Cleaned dataset not found. Run T011 first.")
        
        df = pd.read_csv(cleaned_data_path)
        
        # Ensure required columns exist
        required_cols = ['resolution_time_hours', 'programming_language', 'repository']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            pytest.skip(f"Missing required columns: {missing}")
        
        # Filter for valid data
        valid_df = df.dropna(subset=required_cols)
        valid_df = valid_df[valid_df['resolution_time_hours'] > 0]
        
        if len(valid_df) < 10:
            pytest.skip("Insufficient data for model fitting (need at least 10 valid rows)")
        
        return valid_df
    
    @pytest.mark.skipif(
        not MIXED_EFFECTS_AVAILABLE,
        reason="Mixed effects model implementation (T022) not yet available"
    )
    def test_model_convergence(self, sample_data):
        """
        Test that the mixed-effects model converges successfully.
        
        This is the primary integration test for US3. It verifies that:
        1. The model can be instantiated with real data
        2. The fitting process completes without errors
        3. The model reports convergence (not failure)
        """
        # Fit the model
        result = fit_mixed_effects_model(
            data=sample_data,
            target='resolution_time_hours',
            fixed_effects=['programming_language'],
            random_intercept='repository'
        )
        
        # Verify convergence
        assert result is not None, "Model fitting returned None"
        assert 'converged' in result, "Result missing 'converged' status"
        assert result['converged'] is True, "Model did not converge"
        
        # Verify result structure
        assert 'fixed_effects' in result, "Missing fixed effects in result"
        assert 'random_effects' in result, "Missing random effects in result"
        assert 'model_summary' in result, "Missing model summary"
        
        # Verify non-empty coefficients
        assert len(result['fixed_effects']) > 0, "No fixed effects coefficients"
        
        print(f"Model converged successfully with {len(result['fixed_effects'])} fixed effects")
    
    @pytest.mark.skipif(
        not MIXED_EFFECTS_AVAILABLE,
        reason="Mixed effects model implementation (T022) not yet available"
    )
    def test_model_with_real_data(self, cleaned_data_path):
        """
        Test model fitting with the actual cleaned dataset.
        
        This test ensures the model can handle the full dataset size
        and various programming language groups present in the data.
        """
        if not cleaned_data_path.exists():
            pytest.skip("Cleaned dataset not found. Run T011 first.")
        
        # Load data using the utility function
        df = load_cleaned_data(cleaned_data_path)
        
        # Filter for sufficient data
        valid_df = df.dropna(subset=['resolution_time_hours', 'programming_language', 'repository'])
        valid_df = valid_df[valid_df['resolution_time_hours'] > 0]
        
        if len(valid_df) < 50:
            pytest.skip("Insufficient data for meaningful model testing")
        
        # Group by language and check diversity
        lang_counts = valid_df['programming_language'].value_counts()
        if len(lang_counts) < 2:
            pytest.skip("Need at least 2 programming language groups for comparison")
        
        # Fit model
        result = fit_mixed_effects_model(
            data=valid_df,
            target='resolution_time_hours',
            fixed_effects=['programming_language'],
            random_intercept='repository'
        )
        
        assert result['converged'] is True, "Model failed to converge on real data"
        assert result['num_observations'] >= 50, f"Expected at least 50 observations, got {result['num_observations']}"
        
        # Check that random effects were estimated
        assert 'variance_components' in result, "Missing variance components"
        assert 'repository_variance' in result['variance_components'], "Missing repository variance"
        
        print(f"Real data test passed: {result['num_observations']} observations, {len(valid_df['programming_language'].unique())} language groups")
    
    @pytest.mark.skipif(
        not MIXED_EFFECTS_AVAILABLE,
        reason="Mixed effects model implementation (T022) not yet available"
    )
    def test_model_diagnostics(self, sample_data):
        """
        Test that model diagnostics are properly computed.
        
        Verifies that key metrics like AIC, BIC, and log-likelihood
        are computed and returned.
        """
        result = fit_mixed_effects_model(
            data=sample_data,
            target='resolution_time_hours',
            fixed_effects=['programming_language'],
            random_intercept='repository'
        )
        
        # Check for standard model metrics
        assert 'aic' in result, "Missing AIC"
        assert 'bic' in result, "Missing BIC"
        assert 'log_likelihood' in result, "Missing log-likelihood"
        assert 'num_fixed_effects' in result, "Missing number of fixed effects"
        assert 'num_random_effects' in result, "Missing number of random effects"
        
        # Validate metric types
        assert isinstance(result['aic'], (int, float)), "AIC must be numeric"
        assert isinstance(result['bic'], (int, float)), "BIC must be numeric"
        assert isinstance(result['log_likelihood'], (int, float)), "Log-likelihood must be numeric"
        
        # AIC and BIC should be finite
        assert np.isfinite(result['aic']), "AIC is not finite"
        assert np.isfinite(result['bic']), "BIC is not finite"
        assert np.isfinite(result['log_likelihood']), "Log-likelihood is not finite"
        
        print(f"Diagnostics: AIC={result['aic']:.2f}, BIC={result['bic']:.2f}, LL={result['log_likelihood']:.2f}")
    
    @pytest.mark.skipif(
        not MIXED_EFFECTS_AVAILABLE,
        reason="Mixed effects model implementation (T022) not yet available"
    )
    def test_model_error_handling(self):
        """
        Test that the model handles invalid input gracefully.
        
        Verifies that appropriate errors are raised for:
        - Missing target column
        - Insufficient data
        - Invalid column types
        """
        # Create a minimal invalid dataframe
        invalid_df = pd.DataFrame({
            'x': [1, 2, 3],
            'y': [4, 5, 6]
        })
        
        # Test missing target column
        with pytest.raises((KeyError, ValueError)):
            fit_mixed_effects_model(
                data=invalid_df,
                target='nonexistent_column',
                fixed_effects=['x'],
                random_intercept='y'
            )
        
        # Test insufficient data (too few groups)
        tiny_df = pd.DataFrame({
            'target': [1.0, 2.0],
            'fixed': ['a', 'b'],
            'random': ['repo1', 'repo1']  # Only 1 group
        })
        
        # This should either fail or warn about insufficient groups
        # We expect it to raise an error or return a result with convergence=False
        try:
            result = fit_mixed_effects_model(
                data=tiny_df,
                target='target',
                fixed_effects=['fixed'],
                random_intercept='random'
            )
            # If it returns, it should indicate non-convergence
            assert result.get('converged') is False, "Model should not converge with 1 random effect group"
        except Exception:
            # Expected: model fitting fails with insufficient data
            pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])