"""
Test script for Zero-Flux Event Handling Verification (T055).

This test injects rows with zero flux for heavy nuclei into a mock dataset
and verifies that `preprocess.py` correctly logs these as "Below Detection Limit"
and excludes them from ratio calculations without causing a division-by-zero error
or skewing the mean.

Constraints:
- Output ratio for zero-flux row must be NaN.
- Log must contain the specific "Below Detection Limit" message.
"""
import os
import sys
import logging
import io
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.data.preprocess import calculate_composition_ratios
from code.utils.logging import setup_logger, log_below_detection_limit

def test_zero_flux_handling():
    """
    Test that zero flux values in denominator or numerator are handled correctly.
    """
    # Setup logging to capture output
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.INFO)
    
    # Create a temporary directory for output
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_output.csv"
        log_file = Path(tmpdir) / "test.log"
        
        # Setup logger for the module
        logger = setup_logger("test_zero_flux", log_file=str(log_file), level=logging.INFO)
        
        # Create mock data
        # We need: date, rigidity_bin, proton_flux, helium_flux, iron_flux, sunspot_number
        # Scenario 1: Proton flux is 0 (Denominator zero -> Ratio NaN)
        # Scenario 2: Helium flux is 0 (Numerator zero -> Ratio 0.0)
        # Scenario 3: Iron flux is 0 (Numerator zero -> Ratio 0.0)
        
        data = {
            'date': pd.date_range(start='2020-01-01', periods=5, freq='D'),
            'rigidity_bin': [1.0, 1.0, 1.0, 1.0, 1.0],
            'proton_flux': [100.0, 0.0, 100.0, 100.0, 100.0],  # Row 1 has 0 proton flux
            'helium_flux': [10.0, 5.0, 0.0, 10.0, 10.0],      # Row 2 has 0 helium flux
            'iron_flux': [1.0, 0.5, 0.0, 0.0, 1.0],           # Row 2 has 0 iron flux
            'sunspot_number': [50, 51, 52, 53, 54]
        }
        
        df = pd.DataFrame(data)
        
        # Run the preprocessing function
        # This function should handle the zero flux cases
        result_df = calculate_composition_ratios(df, output_path=str(output_path))
        
        # Assertions
        assert result_df is not None, "Result dataframe should not be None"
        assert 'He_p_ratio' in result_df.columns, "He_p_ratio column must exist"
        assert 'Fe_p_ratio' in result_df.columns, "Fe_p_ratio column must exist"
        
        # Check Row 1: Proton flux is 0 -> He/p and Fe/p should be NaN
        row1_he = result_df.iloc[0]['He_p_ratio']
        row1_fe = result_df.iloc[0]['Fe_p_ratio']
        
        assert np.isnan(row1_he), f"Expected NaN for He/p when proton flux is 0, got {row1_he}"
        assert np.isnan(row1_fe), f"Expected NaN for Fe/p when proton flux is 0, got {row1_fe}"
        
        # Check Row 2: Proton flux is valid, Helium is 0 -> He/p should be 0.0
        row2_he = result_df.iloc[1]['He_p_ratio']
        row2_fe = result_df.iloc[1]['Fe_p_ratio']
        
        assert row2_he == 0.0, f"Expected 0.0 for He/p when helium flux is 0, got {row2_he}"
        assert row2_fe == 0.0, f"Expected 0.0 for Fe/p when iron flux is 0, got {row2_fe}"
        
        # Check Row 3: Proton flux valid, Iron is 0 -> Fe/p should be 0.0
        row3_fe = result_df.iloc[2]['Fe_p_ratio']
        assert row3_fe == 0.0, f"Expected 0.0 for Fe/p when iron flux is 0, got {row3_fe}"
        
        # Verify mean is not skewed by division by zero (should be calculated only on valid rows)
        # Mean of He/p: (10/100 + 5/0 + 0/100 + 10/100 + 10/100) -> (0.1 + NaN + 0.0 + 0.1 + 0.1)
        # Mean should ignore NaN
        mean_he = result_df['He_p_ratio'].mean()
        # Valid rows: 0.1 (row0), 0.0 (row2), 0.1 (row3), 0.1 (row4) -> sum 0.3 / 4 = 0.075
        expected_mean = 0.075
        assert np.isclose(mean_he, expected_mean), f"Expected mean {expected_mean}, got {mean_he}"
        
        # Verify log file contains "Below Detection Limit"
        log_content = log_file.read_text()
        assert "Below Detection Limit" in log_content, \
            f"Log must contain 'Below Detection Limit', but found: {log_content}"
        
        # Verify the specific message for proton flux zero
        assert "proton flux is zero" in log_content.lower() or "denominator" in log_content.lower(), \
            "Log should indicate the cause of the below detection limit event"

        print("Test passed: Zero flux handling is correct.")

if __name__ == "__main__":
    test_zero_flux_handling()
    print("All assertions passed.")