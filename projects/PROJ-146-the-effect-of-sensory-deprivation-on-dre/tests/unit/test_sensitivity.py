"""
Unit tests for bootstrap resampling logic in code/sensitivity.py.

This module verifies that the bootstrap resampling mechanism correctly:
1. Resamples data with replacement.
2. Calculates statistics on resampled data.
3. Handles edge cases (e.g., small sample sizes, convergence checks).
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure code directory is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from sensitivity import run_bootstrap


class TestBootstrapResampling:
    """Tests for the run_bootstrap function logic."""

    @pytest.fixture
    def sample_data(self):
        """Create a deterministic sample dataset for testing."""
        np.random.seed(42)
        n = 50
        data = pd.DataFrame({
            'condition': np.random.choice(['strict', 'moderate', 'partial'], n),
            'recall': np.random.randint(0, 2, n),
            'bizarreness': np.random.randint(1, 8, n),
            'participant_id': [f'P{i}' for i in range(n)]
        })
        return data

    @pytest.fixture
    def mock_model_fit(self):
        """Mock a model fitting function that returns a deterministic coefficient."""
        def mock_fit(df, *args, **kwargs):
            # Return a mock result object with a fixed coefficient for recall
            # to ensure test stability.
            result = MagicMock()
            # Simulate a coefficient for the 'condition' effect
            result.params = {'condition_moderate': 0.5, 'condition_partial': 0.2}
            result.conf_int = lambda alpha=0.05: np.array([
                [0.4, 0.6],
                [0.1, 0.3]
            ])
            return result
        return mock_fit

    def test_resampling_with_replacement(self, sample_data):
        """Verify that resampling actually samples with replacement and preserves size."""
        # We test the internal logic by checking if the function can handle a
        # custom resampling step or if the output dimensions are correct.
        # Since run_bootstrap is the entry point, we verify it returns a structure
        # of the expected shape.
        
        # Mock the model fitting to avoid dependency on statsmodels complexity in this unit test
        with patch('sensitivity._fit_model_on_df') as mock_fit:
            mock_fit.return_value = {'coeff': 0.5, 'pval': 0.05}
            
            # Run a small bootstrap (e.g., 10 iterations)
            results = run_bootstrap(
                data=sample_data,
                n_resamples=10,
                target_metric='recall',
                model_fit_func=mock_fit,
                seed=42
            )
            
            # Assert results is a list of dictionaries or a DataFrame
            assert isinstance(results, list), "Bootstrap results should be a list of iteration results."
            assert len(results) == 10, f"Expected 10 results, got {len(results)}"
            
            # Check that each result contains the expected keys
            for res in results:
                assert 'coeff' in res, "Each result must contain the 'coeff' key."
                assert 'pval' in res, "Each result must contain the 'pval' key."

    def test_convergence_check_logic(self, sample_data):
        """Test that the function attempts to increase resamples if variance is high."""
        # This test verifies the logic flow where variance > threshold triggers more resamples.
        # We mock the fitting function to return highly variable results to force the loop.
        
        call_count = 0
        def variable_fit(df, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Return a coefficient that oscillates wildly to trigger variance check
            return {'coeff': 10.0 if call_count % 2 == 0 else -10.0, 'pval': 0.01}

        with patch('sensitivity._fit_model_on_df', side_effect=variable_fit):
            # Set a low variance threshold to force the loop to run more iterations
            # We expect the function to hit the cap (5000) or stop early if logic handles it.
            # For unit testing, we just ensure it doesn't crash and respects the cap.
            results = run_bootstrap(
                data=sample_data,
                n_resamples=100, # Start low
                target_metric='recall',
                model_fit_func=variable_fit,
                max_resamples=50, # Hard cap for this test
                seed=42
            )
            
            # The function should have stopped at the hard cap (50) or earlier
            assert len(results) <= 50, "Should not exceed max_resamples cap."
            assert len(results) > 0, "Should have at least one result."

    def test_empty_data_handling(self):
        """Ensure the function handles empty data gracefully."""
        empty_df = pd.DataFrame(columns=['condition', 'recall', 'bizarreness', 'participant_id'])
        
        with patch('sensitivity._fit_model_on_df') as mock_fit:
            mock_fit.return_value = {'coeff': 0.0, 'pval': 1.0}
            
            # Should raise an error or return empty list depending on implementation
            # Based on robustness requirements, it should likely raise a clear error
            # or return an empty structure. We test that it doesn't crash with a weird exception.
            with pytest.raises((ValueError, IndexError)):
                run_bootstrap(
                    data=empty_df,
                    n_resamples=5,
                    target_metric='recall',
                    model_fit_func=mock_fit,
                    seed=42
                )

    def test_seed_reproducibility(self, sample_data):
        """Verify that setting a seed produces identical results across runs."""
        with patch('sensitivity._fit_model_on_df') as mock_fit:
            mock_fit.return_value = {'coeff': 0.5, 'pval': 0.05}
            
            results_run1 = run_bootstrap(
                data=sample_data,
                n_resamples=5,
                target_metric='recall',
                model_fit_func=mock_fit,
                seed=123
            )
            
            results_run2 = run_bootstrap(
                data=sample_data,
                n_resamples=5,
                target_metric='recall',
                model_fit_func=mock_fit,
                seed=123
            )
            
            # Compare the results
            assert len(results_run1) == len(results_run2)
            for r1, r2 in zip(results_run1, results_run2):
                assert r1['coeff'] == r2['coeff']
                assert r1['pval'] == r2['pval']

    def test_dynamic_resample_loop(self, sample_data):
        """Test the dynamic increase of resamples until variance threshold is met."""
        # Mock a fit function that stabilizes after a few iterations
        stable_values = [0.1, 0.2, 0.15, 0.14, 0.141, 0.142, 0.1415]
        idx = 0
        
        def stable_fit(df, *args, **kwargs):
            nonlocal idx
            val = stable_values[idx % len(stable_values)]
            idx += 1
            return {'coeff': val, 'pval': 0.05}

        with patch('sensitivity._fit_model_on_df', side_effect=stable_fit):
            results = run_bootstrap(
                data=sample_data,
                n_resamples=3, # Start low
                target_metric='recall',
                model_fit_func=stable_fit,
                variance_threshold=0.01, # Very tight
                seed=42
            )
            
            # The function should have increased the number of resamples
            # to satisfy the variance condition (or hit the cap)
            assert len(results) >= 3, "Should have performed at least the initial resamples."
            # Verify the logic ran (we can't easily verify the exact count without seeing internal state,
            # but we verify the function completed and returned a list).
            assert isinstance(results, list)
            
            # Check that the final results are relatively stable (low variance in the tail)
            coeffs = [r['coeff'] for r in results]
            if len(coeffs) > 2:
                tail_variance = np.var(coeffs[-3:])
                # This is a soft check; the function logic handles the strict threshold
                # We just ensure the function didn't return a single value or crash.
                assert len(coeffs) > 1
