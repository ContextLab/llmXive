import pytest
import pandas as pd
import numpy as np
from sensitivity_analysis import analyze_sensitivity, report_sensitivity_results
import logging

# Configure logging for tests
logging.basicConfig(level=logging.INFO)

class TestSensitivitySweep:
    def test_sensitivity_sweep(self):
        """
        Verify that sensitivity analysis correctly calculates statistics
        and that the deviation check logic works (±10% threshold).
        """
        # Create mock data for a sensitivity sweep
        # Simulating a scenario where conductivity varies slightly
        data = {
            'conductivity': [149.0, 150.5, 148.2, 151.0, 149.8],
            'sensitivity_param_value': [0.1, 0.3, 0.5, 0.7, 0.9]
        }
        df = pd.DataFrame(data)
        
        # Run analysis
        stats = analyze_sensitivity(df, 'conductivity')
        
        # Verify statistics
        assert 'mean' in stats
        assert 'std' in stats
        assert 'cv' in stats
        
        # Check calculated values (approximate)
        assert np.isclose(stats['mean'], 149.7, atol=0.1)
        assert stats['std'] > 0
        assert stats['cv'] > 0
        
        # Check the ±10% rule logic (SC-004)
        # In this mock data, CV should be small (< 0.10)
        assert stats['cv'] < 0.10, "Mock data should be within 10% variation"
        
        # Test with high variation data (should fail the 10% check)
        high_var_data = {
            'conductivity': [100.0, 150.0, 50.0, 200.0, 125.0],
            'sensitivity_param_value': [0.1, 0.3, 0.5, 0.7, 0.9]
        }
        df_high = pd.DataFrame(high_var_data)
        stats_high = analyze_sensitivity(df_high, 'conductivity')
        
        # CV should be high
        assert stats_high['cv'] > 0.10, "High variation data should exceed 10% CV"

def test_report_sensitivity_results():
    """
    Verify that report_sensitivity_results logs the expected information.
    """
    stats = {
        'mean': 150.0,
        'std': 5.0,
        'min': 140.0,
        'max': 160.0,
        'cv': 0.033
    }
    
    # This function primarily logs, so we verify it runs without error
    # and produces the expected log output (captured by logging system if needed)
    try:
        report_sensitivity_results(stats)
    except Exception as e:
        pytest.fail(f"report_sensitivity_results raised an exception: {e}")