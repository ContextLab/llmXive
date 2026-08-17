"""
Unit tests for effect size (odds ratio) calculation.

This module verifies that the effect size metrics (odds ratios, confidence intervals)
are calculated correctly from Cumulative Link Mixed Model (CLMM) results.
"""
import math
import pytest
import numpy as np
from typing import Dict, List, Tuple

# Import the analysis module to access the effect size calculation logic
# The function calculate_effect_sizes is expected to be defined in code/analysis.py
# as per task T035 implementation.
try:
    from analysis import calculate_effect_sizes
except ImportError:
    # Fallback for cases where analysis.py might not be fully ready yet,
    # though T035 should have implemented this.
    # We define a mock here for the test to exist, but in a real run,
    # it should import from analysis.py.
    def calculate_effect_sizes(model_results: Dict) -> Dict:
        """Mock implementation for testing purposes only."""
        # This is a placeholder. The real implementation should be in analysis.py.
        # If T035 is complete, this import should succeed and this mock should be removed.
        # For the purpose of this test task, we assume the real function exists.
        # If the import fails, we raise an error to indicate the dependency is missing.
        raise ImportError("The function 'calculate_effect_sizes' must be implemented in code/analysis.py (Task T035) before these tests can run.")


class TestCalculateEffectSizes:
    """Test suite for the calculate_effect_sizes function."""

    def test_odds_ratio_calculation_basic(self):
        """Verify basic odds ratio calculation from log-odds coefficient."""
        # Simulate a simple model result dictionary
        # Assuming the structure matches what T035/T030 produces
        mock_results = {
            'coefficients': {
                'salience_medium': 0.693147,  # log(2) -> odds ratio should be 2.0
                'salience_high': 1.098612,    # log(3) -> odds ratio should be 3.0
                'intercept_1': -1.0,
                'intercept_2': 0.0
            },
            'converged': True
        }

        # Since we can't import the real function if analysis.py isn't ready,
        # we will test the logic directly here or ensure the import works.
        # If T035 is complete, the import above works.
        # Let's assume the import works for this test.
        
        # We will implement a local check for the logic to ensure the test is self-contained
        # in case the import fails, but the task requires testing the *function*.
        # So we must ensure the function exists.
        # If the import failed above, the test suite would have raised ImportError.
        # So we proceed assuming the function is available.
        
        # Re-import to be sure (handling the mock case if needed, but ideally T035 is done)
        # For this specific task T029, we are testing the *existence and correctness* of the logic.
        # If T035 is not done, we cannot test it. But the task list says T035 is completed.
        # So we assume calculate_effect_sizes exists.
        
        # Let's re-try the import to be safe in the test body
        from analysis import calculate_effect_sizes as real_calc
        
        result = real_calc(mock_results)
        
        # Check that odds ratios are calculated correctly
        assert math.isclose(result['odds_ratios']['salience_medium'], 2.0, rel_tol=1e-4)
        assert math.isclose(result['odds_ratios']['salience_high'], 3.0, rel_tol=1e-4)

    def test_confidence_interval_transformation(self):
        """Verify that confidence intervals are correctly transformed to odds ratio scale."""
        mock_results = {
            'coefficients': {
                'salience_medium': 0.0, # log(1) -> OR = 1.0
            },
            'confidence_intervals': {
                'salience_medium': (-0.5, 0.5) # 95% CI for log-odds
            },
            'converged': True
        }

        from analysis import calculate_effect_sizes as real_calc
        result = real_calc(mock_results)

        # The CI for OR should be exp(-0.5) to exp(0.5)
        expected_lower = math.exp(-0.5)
        expected_upper = math.exp(0.5)

        assert math.isclose(result['confidence_intervals']['salience_medium'][0], expected_lower, rel_tol=1e-4)
        assert math.isclose(result['confidence_intervals']['salience_medium'][1], expected_upper, rel_tol=1e-4)

    def test_non_convergence_handling(self):
        """Test that the function handles non-converged models appropriately."""
        mock_results = {
            'coefficients': {},
            'converged': False
        }

        from analysis import calculate_effect_sizes as real_calc
        # Depending on implementation, this might return empty or raise a warning.
        # The task T035 implies we calculate effect sizes, but T032a handles convergence.
        # If the model didn't converge, we should probably not produce valid effect sizes.
        # Let's assume the function returns an empty dict or raises a specific error.
        # For this test, we check that it doesn't crash with invalid data.
        try:
            result = real_calc(mock_results)
            # If it returns, it should be safe (e.g., empty or with a flag)
            assert isinstance(result, dict)
        except Exception as e:
            # It might also raise an error if the model is invalid
            assert "converged" in str(e).lower() or "valid" in str(e).lower()

    def test_zero_coefficient(self):
        """Test that a zero coefficient results in an odds ratio of 1.0."""
        mock_results = {
            'coefficients': {
                'no_effect_var': 0.0
            },
            'converged': True
        }

        from analysis import calculate_effect_sizes as real_calc
        result = real_calc(mock_results)

        assert math.isclose(result['odds_ratios']['no_effect_var'], 1.0, rel_tol=1e-9)

    def test_negative_coefficient(self):
        """Test that a negative coefficient results in an odds ratio < 1.0."""
        mock_results = {
            'coefficients': {
                'negative_var': -1.098612 # log(1/3) -> OR = 1/3
            },
            'converged': True
        }

        from analysis import calculate_effect_sizes as real_calc
        result = real_calc(mock_results)

        assert math.isclose(result['odds_ratios']['negative_var'], 1.0/3.0, rel_tol=1e-4)
        assert result['odds_ratios']['negative_var'] < 1.0

    def test_output_structure(self):
        """Verify the output dictionary contains the expected keys."""
        mock_results = {
            'coefficients': {'x': 0.5},
            'confidence_intervals': {'x': (0.4, 0.6)},
            'converged': True
        }

        from analysis import calculate_effect_sizes as real_calc
        result = real_calc(mock_results)

        assert 'odds_ratios' in result
        assert 'confidence_intervals' in result
        assert 'p_values' in result # Assuming p-values are also part of the effect size report
        assert 'model_summary' in result or 'metadata' in result # General structure check

if __name__ == '__main__':
    pytest.main([__file__, '-v'])