import pytest
import pandas as pd
from code.report import load_correlation_results, load_validation_status, load_sensitivity_report

class TestLoadCorrelationResults:
    def test_load_correlation_results_exists(self):
        """Test that load_correlation_results can handle existing file."""
        # This test will fail if the file doesn't exist, which is expected
        # in a real test environment
        try:
            results = load_correlation_results()
            assert isinstance(results, pd.DataFrame)
            assert len(results) > 0
        except FileNotFoundError:
            # Expected if file doesn't exist yet
            pytest.skip("correlation_results.csv not found - expected in development")

    def test_load_correlation_results_structure(self):
        """Test that loaded results have expected columns."""
        try:
            results = load_correlation_results()
            expected_cols = ['variable', 'correlation', 'p_value', 'fdr_p_value']
            for col in expected_cols:
                assert col in results.columns
        except FileNotFoundError:
            pytest.skip("correlation_results.csv not found - expected in development")

class TestLoadValidationStatus:
    def test_load_validation_status_exists(self):
        """Test that load_validation_status can handle existing file."""
        try:
            status = load_validation_status()
            assert isinstance(status, dict)
            assert 'resampling_skipped' in status or 'bootstrap_results' in status
        except FileNotFoundError:
            pytest.skip("validation_status.json not found - expected in development")

    def test_load_validation_status_structure(self):
        """Test that loaded status has expected fields."""
        try:
            status = load_validation_status()
            assert isinstance(status, dict)
            # Check for expected keys
            assert any(key in status for key in ['resampling_skipped', 'bootstrap_results', 'sensitivity_results'])
        except FileNotFoundError:
            pytest.skip("validation_status.json not found - expected in development")

class TestLoadSensitivityReport:
    def test_load_sensitivity_report_exists(self):
        """Test that load_sensitivity_report can handle existing file."""
        try:
            report = load_sensitivity_report()
            assert isinstance(report, pd.DataFrame)
            assert len(report) > 0
        except FileNotFoundError:
            pytest.skip("sensitivity_report.csv not found - expected in development")

    def test_load_sensitivity_report_structure(self):
        """Test that loaded report has expected columns."""
        try:
            report = load_sensitivity_report()
            expected_cols = ['threshold', 'significant_count']
            for col in expected_cols:
                assert col in report.columns
        except FileNotFoundError:
            pytest.skip("sensitivity_report.csv not found - expected in development")