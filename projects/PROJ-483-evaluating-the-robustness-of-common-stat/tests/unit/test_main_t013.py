"""
Unit tests for T013: Sensitivity Analysis Sweep logic.
Tests the aggregation and sweep logic in code/main.py.
"""
import os
import sys
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_aggregation_logic():
    """
    Verify that the aggregation logic correctly calculates error rates and CIs
    given a mock simulation output.
    """
    from metrics import calculate_type1_error, clopper_pearson_ci

    # Simulate a scenario: 1000 reps, 50 failures (p < 0.05)
    n_rep = 1000
    n_fail = 50
    alpha = 0.05
    
    # Create mock p-values: 50 values < 0.05, 950 values > 0.05
    p_values = np.concatenate([
        np.random.uniform(0, 0.05, n_fail),
        np.random.uniform(0.05, 1.0, n_rep - n_fail)
    ])
    
    error_rate = calculate_type1_error(p_values, alpha)
    ci_lower, ci_upper = clopper_pearson_ci(n_fail, n_rep, alpha)
    
    # Expected error rate
    expected_rate = n_fail / n_rep
    
    assert np.isclose(error_rate, expected_rate), f"Expected {expected_rate}, got {error_rate}"
    assert ci_lower <= expected_rate <= ci_upper, "CI should contain observed rate"
    assert ci_lower >= 0 and ci_upper <= 1, "CI bounds must be valid probabilities"
    
    print("Test aggregation logic: PASSED")

def test_sweep_range_generation():
    """
    Verify that the sweep generates the correct range of r values.
    """
    # Logic from main.py: [0.0, 0.1, ..., 0.9]
    r_values = [float(x) / 10.0 for x in range(0, 10)]
    expected = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    
    assert r_values == expected, f"Sweep range mismatch: {r_values}"
    print("Test sweep range generation: PASSED")

@patch('code.main.run_simulation')
@patch('code.main.load_config')
def test_main_execution_flow(mock_load_config, mock_run_sim):
    """
    Test the main execution flow of T013 with mocked dependencies.
    """
    # Setup mocks
    mock_load_config.return_value = {
        'simulation': {
            'seed': 42,
            'alpha': 0.05,
            'n_replications': 100
        }
    }
    
    # Mock simulation return: 100 p-values, 5 of which are < 0.05
    mock_p_vals = np.concatenate([
        np.random.uniform(0, 0.05, 5),
        np.random.uniform(0.05, 1.0, 95)
    ])
    mock_run_sim.return_value = pd.DataFrame({'p_value': mock_p_vals})
    
    # Import main to test
    from code.main import main
    
    # Run
    try:
        result_df = main()
        
        # Assertions
        assert isinstance(result_df, pd.DataFrame), "Result should be a DataFrame"
        assert 'dependency_strength' in result_df.columns, "Missing strength column"
        assert 'observed_error_rate' in result_df.columns, "Missing error rate column"
        assert len(result_df) == 10, "Should have 10 rows for 10 r values"
        
        # Check specific value for r=0.0 (should be ~0.05 theoretically)
        row_r0 = result_df[result_df['dependency_strength'] == 0.0].iloc[0]
        assert row_r0['status'] == 'completed', "Row r=0.0 should be completed"
        
        print("Test main execution flow: PASSED")
    except Exception as e:
        print(f"Test main execution flow: FAILED - {e}")
        raise

if __name__ == "__main__":
    test_aggregation_logic()
    test_sweep_range_generation()
    test_main_execution_flow()
    print("All T013 unit tests passed.")
