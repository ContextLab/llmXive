"""Tests for T023: Sensitivity Analysis."""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from sensitivity_analysis import run_sensitivity_analysis, generate_sensitivity_table
from utils.logging import get_logger

def test_run_sensitivity_analysis_counts():
    """Test that sensitivity analysis correctly counts significant electrodes."""
    # Create mock data
    data = {
        'channel': ['Fz', 'Cz', 'Pz', 'Oz', 'F3', 'F4', 'C3', 'C4', 'P3', 'P4'],
        'p_value_bh': [0.01, 0.03, 0.04, 0.06, 0.005, 0.02, 0.08, 0.09, 0.015, 0.10]
    }
    df = pd.DataFrame(data)

    # Run analysis
    result = run_sensitivity_analysis(df)

    # Expected: 
    # <= 0.05: Fz(0.01), Cz(0.03), Pz(0.04), F3(0.005), F4(0.02), P3(0.015) = 6
    # <= 0.01: Fz(0.01), F3(0.005) = 2
    
    sig_05 = result[result['threshold'] == 0.05]['significant_electrodes'].iloc[0]
    sig_01 = result[result['threshold'] == 0.01]['significant_electrodes'].iloc[0]

    assert sig_05 == 6, f"Expected 6 significant at 0.05, got {sig_05}"
    assert sig_01 == 2, f"Expected 2 significant at 0.01, got {sig_01}"
    assert len(result) == 2, "Result should have 2 rows (one per threshold)"

def test_generate_sensitivity_table_writes_file(tmp_path):
    """Test that generate_sensitivity_table writes the correct file."""
    # Temporarily override OUTPUT_FILE
    import sensitivity_analysis
    original_output = sensitivity_analysis.OUTPUT_FILE
    test_output = tmp_path / "test_sensitivity_table.csv"
    sensitivity_analysis.OUTPUT_FILE = test_output

    try:
        data = {
            'channel': ['Fz', 'Cz', 'Pz'],
            'p_value_bh': [0.04, 0.06, 0.02]
        }
        df = pd.DataFrame(data)

        result = generate_sensitivity_table(df)

        assert test_output.exists(), "Output file was not created"
        
        # Verify content
        written_df = pd.read_csv(test_output)
        assert 'threshold' in written_df.columns
        assert 'significant_electrodes' in written_df.columns
        assert len(written_df) == 2
        
        # Check counts: 0.05 -> 2 (Fz, Pz), 0.01 -> 0
        sig_05 = written_df[written_df['threshold'] == 0.05]['significant_electrodes'].iloc[0]
        assert sig_05 == 2, f"Expected 2 significant at 0.05, got {sig_05}"
    finally:
        sensitivity_analysis.OUTPUT_FILE = original_output
