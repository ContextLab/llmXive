import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from sensitivity_analysis import run_sensitivity_analysis, generate_sensitivity_table

class TestSensitivityAnalysis:
    def test_sensitivity_counts_correct(self, tmp_path):
        """
        Test that the sensitivity analysis correctly counts significant electrodes
        at p <= 0.05 and p <= 0.01 thresholds.
        """
        # Create mock data with known p-values
        # 10 channels: 5 significant at 0.05, 2 significant at 0.01
        mock_data = pd.DataFrame({
            'channel': [f'ch_{i}' for i in range(10)],
            'p_value': [0.04, 0.03, 0.02, 0.01, 0.005, 0.06, 0.07, 0.08, 0.09, 0.10]
        })
        
        thresholds = [0.05, 0.01]
        results = run_sensitivity_analysis(mock_data, thresholds)
        
        # Verify structure
        assert len(results) == 2
        assert results[0]['threshold'] == 0.05
        assert results[1]['threshold'] == 0.01
        
        # Verify counts
        # At 0.05: 0.04, 0.03, 0.02, 0.01, 0.005 -> 5
        assert results[0]['count_significant'] == 5
        # At 0.01: 0.01, 0.005 -> 2
        assert results[1]['count_significant'] == 2

    def test_empty_dataframe(self, tmp_path):
        """Test handling of empty results dataframe."""
        empty_df = pd.DataFrame(columns=['channel', 'p_value'])
        thresholds = [0.05, 0.01]
        results = run_sensitivity_analysis(empty_df, thresholds)
        
        assert len(results) == 2
        assert results[0]['count_significant'] == 0
        assert results[1]['count_significant'] == 0

    def test_generate_csv_output(self, tmp_path):
        """Test that the CSV file is generated with correct schema."""
        mock_data = pd.DataFrame({
            'channel': ['ch_A', 'ch_B'],
            'p_value': [0.03, 0.002]
        })
        
        results = run_sensitivity_analysis(mock_data, [0.05, 0.01])
        output_file = tmp_path / "sensitivity_table.csv"
        
        generate_sensitivity_table(results, str(output_file))
        
        assert output_file.exists()
        
        df = pd.read_csv(output_file)
        
        # Verify schema
        assert 'threshold' in df.columns
        assert 'count_significant' in df.columns
        assert list(df.columns) == ['threshold', 'count_significant']
        
        # Verify content
        assert len(df) == 2
        assert df.iloc[0]['count_significant'] == 2 # Both < 0.05
        assert df.iloc[1]['count_significant'] == 1 # Only 0.002 < 0.01