import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from sensitivity_analysis import run_sensitivity_analysis, generate_sensitivity_table, load_analysis_results

class TestSensitivityAnalysis:
    
    @pytest.fixture
    def sample_results(self):
        """Create sample correlation results for testing."""
        return pd.DataFrame({
            'metric_name': ['lzc_f3', 'lzc_f4', 'pe_f3', 'pe_f4', 'lzc_c3', 'lzc_c4'],
            'correlation': [-0.45, -0.52, -0.38, -0.61, -0.29, -0.48],
            'p_value': [0.008, 0.001, 0.035, 0.0002, 0.095, 0.003],
            'fdr_corrected_p': [0.015, 0.003, 0.055, 0.0003, 0.12, 0.006],
            'significant': [True, True, False, True, False, True]
        })

    def test_run_sensitivity_analysis_basic(self, sample_results):
        """Test basic sensitivity analysis execution."""
        result = run_sensitivity_analysis(sample_results, thresholds=[0.05])
        
        assert isinstance(result, pd.DataFrame)
        assert 'threshold' in result.columns
        assert 'metric_name' in result.columns
        assert 'is_significant' in result.columns
        
        # Should have 4 significant findings at p≤0.05 (lzc_f3, lzc_f4, pe_f4, lzc_c4)
        summary = result[result['metric_name'] == '__SUMMARY__']
        assert len(summary) == 1
        assert summary.iloc[0]['total_significant'] == 4

    def test_sensitivity_analysis_multiple_thresholds(self, sample_results):
        """Test sensitivity analysis with multiple thresholds."""
        result = run_sensitivity_analysis(sample_results, thresholds=[0.05, 0.01])
        
        thresholds = sorted(result['threshold'].unique())
        assert len(thresholds) == 2
        assert 0.05 in thresholds
        assert 0.01 in thresholds
        
        # At p≤0.01, fewer should be significant
        summary_05 = result[(result['threshold'] == 0.05) & (result['metric_name'] == '__SUMMARY__')]
        summary_01 = result[(result['threshold'] == 0.01) & (result['metric_name'] == '__SUMMARY__')]
        
        assert summary_05.iloc[0]['total_significant'] >= summary_01.iloc[0]['total_significant']

    def test_sensitivity_analysis_no_significant(self, sample_results):
        """Test when no findings are significant at given threshold."""
        result = run_sensitivity_analysis(sample_results, thresholds=[0.001])
        
        summary = result[result['metric_name'] == '__SUMMARY__']
        assert len(summary) == 1
        assert summary.iloc[0]['total_significant'] == 0

    def test_generate_sensitivity_table_creates_file(self, sample_results, tmp_path):
        """Test that generate_sensitivity_table creates a valid CSV file."""
        sensitivity_df = run_sensitivity_analysis(sample_results, thresholds=[0.05])
        output_path = tmp_path / 'test_sensitivity.csv'
        
        result_path = generate_sensitivity_table(sensitivity_df, output_path)
        
        assert result_path.exists()
        assert result_path.suffix == '.csv'
        
        # Verify CSV can be read
        with open(result_path, 'r') as f:
            content = f.read()
            assert 'Sensitivity Analysis Results' in content
            assert 'Threshold' in content

    def test_proportion_significant_calculation(self, sample_results):
        """Test that proportion significant is calculated correctly."""
        result = run_sensitivity_analysis(sample_results, thresholds=[0.05])
        
        summary = result[result['metric_name'] == '__SUMMARY__']
        assert len(summary) == 1
        
        total = summary.iloc[0]['total_tests']
        sig = summary.iloc[0]['total_significant']
        expected_prop = sig / total if total > 0 else 0.0
        
        assert abs(summary.iloc[0]['proportion_significant'] - expected_prop) < 1e-6

    def test_fdr_corrected_p_usage(self, sample_results):
        """Test that FDR-corrected p-values are used for significance determination."""
        # Create data where raw p < 0.05 but FDR corrected > 0.05
        edge_case = pd.DataFrame({
            'metric_name': ['test_metric'],
            'correlation': [-0.3],
            'p_value': [0.04],  # Significant raw
            'fdr_corrected_p': [0.08],  # Not significant after FDR
            'significant': [True]  # Original flag (may be incorrect)
        })
        
        result = run_sensitivity_analysis(edge_case, thresholds=[0.05])
        
        # Should NOT be counted as significant because FDR corrected > 0.05
        summary = result[result['metric_name'] == '__SUMMARY__']
        assert summary.iloc[0]['total_significant'] == 0
