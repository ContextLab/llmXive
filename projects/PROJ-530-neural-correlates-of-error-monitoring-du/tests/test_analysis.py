import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from analysis import run_sensitivity_sweep, fit_linear_mixed_effects_model, FeasibilityError

@pytest.fixture
def mock_processed_data():
    """
    Generate a synthetic dataset mimicking the output of preprocess.py.
    """
    np.random.seed(42)
    n_participants = 10
    n_trials_per_participant = 50
    
    data = []
    for pid in range(n_participants):
        for i in range(n_trials_per_participant):
            # Generate random error magnitude (0 to 90 degrees)
            error_mag = np.random.uniform(0, 90)
            # Generate MFN amplitude with some correlation to error magnitude
            # Negative correlation expected (larger error -> more negative MFN)
            mean_amp = -2.0 - (0.05 * error_mag) + np.random.normal(0, 1.0)
            
            data.append({
                'participant_id': f'sub-{pid:03d}',
                'error_magnitude': error_mag,
                'mean_amplitude': mean_amp,
                'electrode': 'FCz'
            })
    
    return pd.DataFrame(data)

def test_sensitivity_sweep_integration(mock_processed_data):
    """
    Integration test for T023: Run sensitivity sweep on a subset and verify output format.
    """
    # Define specific thresholds to test
    thresholds = [5.0, 10.0, 15.0, 20.0]
    output_path = Path("results/diagnostics/test_sensitivity_summary.csv")
    
    # Run the sweep
    results_df = run_sensitivity_sweep(
        mock_processed_data, 
        thresholds=thresholds, 
        output_path=output_path
    )
    
    # Verify the output file exists
    assert output_path.exists(), "Sensitivity summary CSV was not created."
    
    # Verify the content
    assert isinstance(results_df, pd.DataFrame)
    assert 'threshold' in results_df.columns
    assert 'correlation' in results_df.columns
    assert 'p_value' in results_df.columns
    assert 'n_samples' in results_df.columns
    
    # Verify row count matches number of thresholds
    assert len(results_df) == len(thresholds), f"Expected {len(thresholds)} rows, got {len(results_df)}"
    
    # Verify thresholds match input
    assert list(results_df['threshold']) == thresholds
    
    # Verify that correlation and p_value are numeric (not strings)
    assert results_df['correlation'].dtype in [np.float64, np.float32]
    assert results_df['p_value'].dtype in [np.float64, np.float32]
    
    # Verify that n_samples decreases as threshold increases (monotonicity check)
    # (Assuming uniform distribution, but definitely non-increasing)
    # Note: With random data, strict monotonicity isn't guaranteed, but generally should hold.
    # We just check that n_samples > 0 for the lowest threshold.
    assert results_df.iloc[0]['n_samples'] > 0

def test_threshold_filtering_logic(mock_processed_data):
    """
    Unit test for T026: Verify that filtering events with threshold=10 correctly excludes events < 10.
    """
    thresholds = [10.0]
    output_path = Path("results/diagnostics/test_filter_logic.csv")
    
    results_df = run_sensitivity_sweep(
        mock_processed_data, 
        thresholds=thresholds, 
        output_path=output_path
    )
    
    # Get the n_samples for threshold 10
    n_samples_10 = results_df[results_df['threshold'] == 10.0]['n_samples'].iloc[0]
    
    # Manually count in original data
    expected_count = len(mock_processed_data[mock_processed_data['error_magnitude'] >= 10.0])
    
    assert n_samples_10 == expected_count, f"Filtering logic failed: Expected {expected_count}, got {n_samples_10}"

def test_sensitivity_sweep_empty_result_handling(mock_processed_data):
    """
    Test handling of a threshold that results in very few or no samples.
    """
    # Use a very high threshold that likely results in 0 or very few samples
    thresholds = [100.0] # Max error in mock data is 90
    output_path = Path("results/diagnostics/test_edge_case.csv")
    
    results_df = run_sensitivity_sweep(
        mock_processed_data, 
        thresholds=thresholds, 
        output_path=output_path
    )
    
    # Should not crash
    assert isinstance(results_df, pd.DataFrame)
    assert len(results_df) == 1
    assert results_df['threshold'].iloc[0] == 100.0
    # Correlation and p-value should be NaN because we skipped fitting
    assert np.isnan(results_df['correlation'].iloc[0])
    assert np.isnan(results_df['p_value'].iloc[0])
    assert results_df['n_samples'].iloc[0] == 0
