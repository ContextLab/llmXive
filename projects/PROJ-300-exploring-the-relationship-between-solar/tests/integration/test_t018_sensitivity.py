"""
Integration tests for T018: Sensitivity Analysis Implementation.
Verifies that the sensitivity table is generated and appended to the JSON report.
"""
import os
import sys
import json
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.main import run_pipeline
from code.analysis.sensitivity import analyze_thresholds

class TestT018Sensitivity:
    
    @pytest.fixture
    def mock_data(self):
        """Create a mock dataset that mimics real data structure."""
        dates = pd.date_range(start='2023-01-01', end='2023-01-03', freq='5min')
        # Generate correlated data with some noise
        vsw = 400 + 100 * np.sin(np.arange(len(dates)) * 0.01) + np.random.normal(0, 20, len(dates))
        # Ensure some values are above 600 for high threshold
        vsw[::10] += 200 
        ey = 0.5 * vsw + np.random.normal(0, 5, len(dates))
        
        df_vsw = pd.DataFrame({'timestamp': dates, 'Vsw': vsw})
        df_ey = pd.DataFrame({'timestamp': dates, 'Ey': ey})
        return df_vsw, df_ey

    @patch('code.main.fetch_omni_sw')
    @patch('code.main.fetch_themis_ey')
    def test_sensitivity_table_in_report(self, mock_themis, mock_omni, mock_data):
        """
        Verify that run_pipeline produces a sensitivity_table in the results.
        SC-003: Generate sensitivity table and append to JSON report.
        """
        df_vsw, df_ey = mock_data
        
        # Mock the fetch functions to return our test data
        mock_omni.return_value = df_vsw
        mock_themis.return_value = df_ey

        # Run the pipeline
        results = run_pipeline('2023-01-01', '2023-01-03')

        # Check that sensitivity_table exists
        assert 'sensitivity_table' in results, "Sensitivity table missing from results"
        assert isinstance(results['sensitivity_table'], list), "Sensitivity table should be a list"
        
        # Verify at least one entry exists (depending on data distribution)
        if len(results['sensitivity_table']) > 0:
            entry = results['sensitivity_table'][0]
            assert 'threshold_kms' in entry, "Missing threshold_kms in sensitivity entry"
            assert 'pearson_r' in entry, "Missing pearson_r in sensitivity entry"
            assert 'n_samples' in entry, "Missing n_samples in sensitivity entry"

    @patch('code.main.fetch_omni_sw')
    @patch('code.main.fetch_themis_ey')
    def test_sensitivity_thresholds_values(self, mock_themis, mock_omni, mock_data):
        """
        Verify that the sensitivity table contains the expected thresholds (400, 500, 600).
        """
        df_vsw, df_ey = mock_data
        mock_omni.return_value = df_vsw
        mock_themis.return_value = df_ey

        results = run_pipeline('2023-01-01', '2023-01-03')

        if len(results['sensitivity_table']) > 0:
            thresholds_found = [entry['threshold_kms'] for entry in results['sensitivity_table']]
            # We expect to see at least some of the defined thresholds
            # (depending on how much data passes the filter)
            expected_thresholds = {400, 500, 600}
            found_set = set(thresholds_found)
            
            # At least one threshold should be present
            assert len(found_set & expected_thresholds) > 0, f"None of expected thresholds {expected_thresholds} found in {thresholds_found}"

    @patch('code.main.fetch_omni_sw')
    @patch('code.main.fetch_themis_ey')
    def test_json_report_written_to_disk(self, mock_themis, mock_omni, mock_data):
        """
        Verify that the JSON report is actually written to disk with the sensitivity table.
        """
        df_vsw, df_ey = mock_data
        mock_omni.return_value = df_vsw
        mock_themis.return_value = df_ey

        # Run pipeline
        results = run_pipeline('2023-01-01', '2023-01-03')

        # Check file existence
        report_path = "projects/PROJ-300-exploring-the-relationship-between-solar/data/processed/us1_correlation.json"
        assert os.path.exists(report_path), f"Report file not found at {report_path}"

        # Verify content
        with open(report_path, 'r') as f:
            saved_results = json.load(f)
        
        assert 'sensitivity_table' in saved_results, "Sensitivity table missing from saved JSON"
        assert saved_results['sensitivity_table'] == results['sensitivity_table'], "Saved sensitivity table differs from in-memory results"

    @patch('code.main.fetch_omni_sw')
    @patch('code.main.fetch_themis_ey')
    def test_sensitivity_with_insufficient_data(self, mock_themis, mock_omni, mock_data):
        """
        Verify that the pipeline handles cases where a threshold has insufficient data
        (should skip or warn, not crash).
        """
        # Create data with very few high speed events
        df_vsw, df_ey = mock_data
        df_vsw['Vsw'] = df_vsw['Vsw'] * 0.5  # Reduce speeds so 600 threshold has no data
        
        mock_omni.return_value = df_vsw
        mock_themis.return_value = df_ey

        # Should not raise an exception
        results = run_pipeline('2023-01-01', '2023-01-03')
        
        # Check that 600 threshold is not in the table or handled gracefully
        if len(results['sensitivity_table']) > 0:
            thresholds = [e['threshold_kms'] for e in results['sensitivity_table']]
            assert 600 not in thresholds, "600 threshold should be skipped if insufficient data"
        
        # Verify quality log has warnings if applicable
        log_path = "projects/PROJ-300-exploring-the-relationship-between-solar/data/processed/quality_log.json"
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                logs = json.load(f)
            # The last log entry should contain warnings if any occurred
            if logs:
                last_log = logs[-1]
                # We don't assert specific warnings here, just that logging works
                assert 'warnings' in last_log