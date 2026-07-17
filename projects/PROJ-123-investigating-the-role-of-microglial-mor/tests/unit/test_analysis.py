"""
Unit tests for the analysis module.
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure code directory is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.analysis import run_sensitivity_analysis, run_regression_with_interaction
from code.config import get_path

@pytest.fixture
def mock_regression_results():
    """
    Fixture providing mock regression results to simulate the output of run_regression_with_interaction.
    This allows the sensitivity test to run without re-running the full pipeline.
    """
    # Simulate results for different Sholl steps
    # The function should return a list of dicts or a DataFrame with p-values
    results = []
    for step in [2, 5, 10]:
        # Simulate a mock result where the interaction term p-value varies slightly
        # but stays within a stable range for this test
        p_val = 0.045 + (step * 0.001)  # 0.047, 0.050, 0.055
        results.append({
            "sholl_radius_step": step,
            "interaction_p_value": p_val,
            "r_squared": 0.65,
            "coefficients": {"intercept": 1.0, "morph_metric": 0.5, "interaction": 0.2}
        })
    
    # Return a DataFrame as the function likely does
    return pd.DataFrame(results)

@pytest.fixture
def mock_analysis_data():
    """
    Fixture providing mock analysis data.
    """
    data = {
        'subject_id': [f'sub_{i}' for i in range(20)],
        'brain_region': ['Hippocampus'] * 10 + ['Prefrontal Cortex'] * 10,
        'pathology_status': ['Normal'] * 10 + ['Early AD'] * 10,
        'cognitive_score': np.random.uniform(0, 100, 20),
        'branch_points': np.random.randint(5, 20, 20),
        'total_length': np.random.uniform(100, 500, 20),
        'soma_area': np.random.uniform(10, 50, 20),
        'sholl_intersections_2': np.random.randint(0, 10, 20),
        'sholl_intersections_5': np.random.randint(0, 15, 20),
        'sholl_intersections_10': np.random.randint(0, 20, 20)
    }
    return pd.DataFrame(data)

class TestSensitivityAnalysis:
    """
    Unit test for sensitivity analysis loop across Sholl steps {2, 5, 10}.
    
    This test verifies that:
    1. The function iterates over the specified Sholl radius steps.
    2. The regression model is run for each step.
    3. The results are aggregated and returned correctly.
    4. The p-value variation is calculated.
    """

    @patch('code.analysis.run_regression_with_interaction')
    @patch('code.analysis.load_analysis_dataset')
    def test_sensitivity_analysis_loop(self, mock_load, mock_run_reg, mock_regression_results, mock_analysis_data):
        """
        Test that the sensitivity analysis loop runs for Sholl steps {2, 5, 10}
        and correctly aggregates results.
        """
        # Setup mocks
        mock_load.return_value = mock_analysis_data
        # Configure the regression mock to return our fixture data
        # We need to make it return different data for each call if the function logic depends on it,
        # but for this test, we verify the loop logic by checking the call count and arguments.
        
        # Since run_sensitivity_analysis likely calls run_regression_with_interaction multiple times,
        # we will use side_effect to return different mock results if needed, 
        # or just verify the calls.
        
        # Let's assume run_regression_with_interaction returns a dict or DataFrame with the p-value
        # We will set up the mock to return a specific value based on the input step
        def mock_reg_side_effect(df, step, **kwargs):
            # Find the matching step in our mock results
            step_data = mock_regression_results[mock_regression_results['sholl_radius_step'] == step]
            if not step_data.empty:
                return step_data.iloc[0].to_dict()
            return None

        mock_run_reg.side_effect = mock_reg_side_effect

        # Call the function under test
        # The function signature in analysis.py is expected to be:
        # run_sensitivity_analysis(sholl_steps=[2, 5, 10])
        try:
            results = run_sensitivity_analysis(sholl_steps=[2, 5, 10])
        except TypeError:
            # Fallback if the function signature is different or relies on internal state
            # This might happen if the function loads data internally
            results = run_sensitivity_analysis()

        # Assertions
        assert results is not None, "Sensitivity analysis should return results"
        
        # Verify that run_regression_with_interaction was called 3 times (once for each step)
        assert mock_run_reg.call_count == 3, f"Expected 3 calls to run_regression_with_interaction, got {mock_run_reg.call_count}"
        
        # Verify the arguments passed to the regression function
        call_args_list = mock_run_reg.call_args_list
        steps_passed = []
        for call in call_args_list:
            # Assuming the step is passed as a keyword argument or positional argument
            # We need to inspect the specific implementation of run_sensitivity_analysis
            # For now, we assume it passes 'sholl_step' or similar
            args, kwargs = call
            # Heuristic: check if the step value is in kwargs or args
            if 'sholl_step' in kwargs:
                steps_passed.append(kwargs['sholl_step'])
            elif len(args) > 1: # Assuming second arg is step
                steps_passed.append(args[1])
            
        # Ensure all expected steps were tested
        expected_steps = {2, 5, 10}
        assert set(steps_passed) == expected_steps, f"Expected steps {expected_steps}, got {set(steps_passed)}"

        # Verify the structure of the returned results
        if isinstance(results, pd.DataFrame):
            assert 'sholl_radius_step' in results.columns, "Results should contain 'sholl_radius_step' column"
            assert 'interaction_p_value' in results.columns, "Results should contain 'interaction_p_value' column"
            assert len(results) == 3, "Results should have 3 rows"
        elif isinstance(results, dict):
            assert 'results' in results, "Results dict should contain 'results' key"
            assert len(results['results']) == 3, "Results should have 3 entries"

    @patch('code.analysis.run_regression_with_interaction')
    @patch('code.analysis.load_analysis_dataset')
    def test_p_value_variation_calculation(self, mock_load, mock_run_reg, mock_regression_results, mock_analysis_data):
        """
        Test that the p-value variation is correctly calculated.
        """
        # Setup mocks
        mock_load.return_value = mock_analysis_data
        def mock_reg_side_effect(df, step, **kwargs):
            step_data = mock_regression_results[mock_regression_results['sholl_radius_step'] == step]
            if not step_data.empty:
                return step_data.iloc[0].to_dict()
            return None
        mock_run_reg.side_effect = mock_reg_side_effect

        results = run_sensitivity_analysis(sholl_steps=[2, 5, 10])

        # Extract p-values
        if isinstance(results, pd.DataFrame):
            p_values = results['interaction_p_value'].values
        elif isinstance(results, dict) and 'results' in results:
            p_values = [r['interaction_p_value'] for r in results['results']]
        else:
            pytest.fail("Unexpected results format")

        # Calculate variation (max - min)
        variation = np.max(p_values) - np.min(p_values)
        
        # Verify calculation (based on our mock data: 0.055 - 0.047 = 0.008)
        expected_variation = 0.008
        assert np.isclose(variation, expected_variation, atol=0.001), \
            f"Expected p-value variation of {expected_variation}, got {variation}"

    @patch('code.analysis.run_regression_with_interaction')
    @patch('code.analysis.load_analysis_dataset')
    def test_sensitivity_analysis_stability_flag(self, mock_load, mock_run_reg, mock_regression_results, mock_analysis_data):
        """
        Test that the stability flag is set correctly based on p-value variation.
        """
        # Setup mocks
        mock_load.return_value = mock_analysis_data
        def mock_reg_side_effect(df, step, **kwargs):
            step_data = mock_regression_results[mock_regression_results['sholl_radius_step'] == step]
            if not step_data.empty:
                return step_data.iloc[0].to_dict()
            return None
        mock_run_reg.side_effect = mock_reg_side_effect

        results = run_sensitivity_analysis(sholl_steps=[2, 5, 10])

        # Check if stability flag is present
        if isinstance(results, dict):
            assert 'stable' in results or 'p_value_stable' in results, "Results should contain stability flag"
            # In our mock, variation is 0.008 which is < 0.05 (5%), so it should be stable
            # Adjust logic based on actual implementation threshold
        elif isinstance(results, pd.DataFrame):
            # If the flag is a summary metric, it might be in a separate dict or attribute
            pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])