import os
import sys
import tempfile
import pytest
from pathlib import Path

import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sensitivity_analysis import run_sensitivity_analysis, generate_sensitivity_table

class TestSensitivityAnalysis:
    
    def test_run_sensitivity_analysis_basic(self):
        """Test basic sensitivity analysis with known data."""
        # Create mock correlation results
        data = {
            'channel': ['Fp1', 'Fp2', 'F3', 'F4', 'C3', 'C4'],
            'correlation': [0.8, 0.75, 0.6, 0.4, 0.3, 0.2],
            'p_value': [0.01, 0.03, 0.04, 0.06, 0.1, 0.2]
        }
        df = pd.DataFrame(data)
        
        # Run analysis
        result = run_sensitivity_analysis(df, thresholds=(0.05, 0.01))
        
        # Verify structure
        assert 'threshold' in result.columns
        assert 'significant_count' in result.columns
        assert 'significance_rate' in result.columns
        
        # Check p<=0.05 results
        row_05 = result[result['threshold'] == 0.05].iloc[0]
        assert row_05['significant_count'] == 4  # Fp1, Fp2, F3, F4
        assert row_05['significance_rate'] == 4/6
        
        # Check p<=0.01 results
        row_01 = result[result['threshold'] == 0.01].iloc[0]
        assert row_01['significant_count'] == 1  # Only Fp1
        assert row_01['significance_rate'] == 1/6

    def test_run_sensitivity_analysis_empty(self):
        """Test sensitivity analysis with empty dataframe."""
        df = pd.DataFrame(columns=['channel', 'correlation', 'p_value'])
        result = run_sensitivity_analysis(df, thresholds=(0.05,))
        
        assert result['significant_count'].iloc[0] == 0
        assert np.isnan(result['mean_correlation_sig'].iloc[0])

    def test_generate_sensitivity_table_file_output(self):
        """Test that generate_sensitivity_table creates a valid CSV file."""
        data = {
            'channel': ['Fp1', 'Fp2', 'F3'],
            'correlation': [0.9, 0.5, 0.1],
            'p_value': [0.001, 0.05, 0.5]
        }
        df = pd.DataFrame(data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "sensitivity_table.csv"
            generate_sensitivity_table(df, output_path)
            
            # Verify file exists
            assert output_path.exists()
            
            # Verify content
            saved_df = pd.read_csv(output_path)
            assert len(saved_df) == 2  # Two thresholds
            assert 'threshold' in saved_df.columns
            assert saved_df['threshold'].tolist() == [0.05, 0.01]

    def test_sensitivity_analysis_edge_case_all_significant(self):
        """Test when all p-values are below threshold."""
        data = {
            'channel': ['A', 'B', 'C'],
            'correlation': [0.5, 0.6, 0.7],
            'p_value': [0.001, 0.002, 0.003]
        }
        df = pd.DataFrame(data)
        
        result = run_sensitivity_analysis(df, thresholds=(0.05,))
        row = result.iloc[0]
        
        assert row['significant_count'] == 3
        assert row['significance_rate'] == 1.0
        assert row['non_significant_count'] == 0

    def test_sensitivity_analysis_edge_case_none_significant(self):
        """Test when no p-values are below threshold."""
        data = {
            'channel': ['A', 'B', 'C'],
            'correlation': [0.1, 0.2, 0.3],
            'p_value': [0.6, 0.7, 0.8]
        }
        df = pd.DataFrame(data)
        
        result = run_sensitivity_analysis(df, thresholds=(0.05,))
        row = result.iloc[0]
        
        assert row['significant_count'] == 0
        assert row['significance_rate'] == 0.0
        assert row['non_significant_count'] == 3