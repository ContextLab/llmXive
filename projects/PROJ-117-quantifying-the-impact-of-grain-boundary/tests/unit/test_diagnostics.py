"""
Unit tests for diagnostics module (T018).
Tests Mutual Information calculation and collinearity diagnostic logic.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.diagnostics import (
    calculate_sigma_from_misorientation,
    compute_mutual_information,
    run_collinearity_diagnostic,
    save_report
)
from code.utils import setup_logging

# Setup logger for tests
logger = setup_logging("test_diagnostics")


class TestCalculateSigmaFromMisorientation:
    """Tests for sigma value calculation logic."""

    def test_sigma_from_valid_misorientation(self):
        """Test sigma calculation with valid misorientation angle."""
        # Typical low-angle grain boundary (e.g., 36.87 degrees for Sigma 3)
        misorientation_angle = 36.87
        sigma = calculate_sigma_from_misorientation(misorientation_angle)
        assert sigma is not None
        assert isinstance(sigma, (int, float))
        assert sigma > 0

    def test_sigma_from_large_angle(self):
        """Test sigma calculation with large misorientation (high sigma)."""
        misorientation_angle = 60.0
        sigma = calculate_sigma_from_misorientation(misorientation_angle)
        assert sigma is not None
        assert sigma > 0

    def test_sigma_from_nan_input(self):
        """Test sigma calculation with NaN input returns None/NaN."""
        misorientation_angle = np.nan
        sigma = calculate_sigma_from_misorientation(misorientation_angle)
        # Should handle NaN gracefully
        assert sigma is None or np.isnan(sigma)


class TestComputeMutualInformation:
    """Tests for Mutual Information calculation."""

    def test_mi_with_dependent_variables(self):
        """Test MI calculation when variables are strongly dependent."""
        # Create synthetic dependent data: y is a function of x
        x = np.linspace(0, 10, 100)
        y = x * 2 + np.random.normal(0, 0.1, 100)  # Strong linear relationship

        mi_score = compute_mutual_information(x, y)
        assert mi_score >= 0
        # With strong dependency, MI should be significantly > 0
        assert mi_score > 0.5

    def test_mi_with_independent_variables(self):
        """Test MI calculation when variables are independent."""
        x = np.random.normal(0, 1, 1000)
        y = np.random.normal(0, 1, 1000)  # Independent of x

        mi_score = compute_mutual_information(x, y)
        assert mi_score >= 0
        # With independence, MI should be close to 0
        assert mi_score < 0.5

    def test_mi_with_constant_variable(self):
        """Test MI calculation with constant variable (edge case)."""
        x = np.ones(100)
        y = np.random.normal(0, 1, 100)

        # Should handle constant variable without crashing
        mi_score = compute_mutual_information(x, y)
        assert mi_score >= 0

    def test_mi_with_nan_values(self):
        """Test MI calculation with NaN values in data."""
        x = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
        y = np.array([2.0, 4.0, 6.0, 8.0, 10.0])

        # Should handle NaN by filtering or returning 0
        mi_score = compute_mutual_information(x, y)
        assert mi_score >= 0

    def test_mi_empty_arrays(self):
        """Test MI calculation with empty arrays."""
        x = np.array([])
        y = np.array([])

        # Should handle empty arrays gracefully
        mi_score = compute_mutual_information(x, y)
        assert mi_score == 0.0 or mi_score is None


class TestRunCollinearityDiagnostic:
    """Tests for the collinearity diagnostic workflow."""

    def test_run_diagnostic_with_valid_data(self):
        """Test diagnostic run with valid misorientation and sigma data."""
        # Create mock data
        data = {
            'misorientation_angle': [36.87, 60.0, 45.0, 30.0, 90.0],
            'sigma_value': [3, 5, 9, 7, 11]
        }

        result = run_collinearity_diagnostic(data)

        assert 'status' in result
        assert 'mi_score' in result
        assert 'interpretation' in result
        assert result['status'] == 'computed'

    def test_run_diagnostic_with_missing_sigma(self):
        """Test diagnostic run when sigma values are missing."""
        # Create mock data with missing sigma
        data = {
            'misorientation_angle': [36.87, 60.0, 45.0],
            'sigma_value': [np.nan, np.nan, np.nan]
        }

        result = run_collinearity_diagnostic(data)

        assert result['status'] == 'unavailable'
        assert 'message' in result
        assert 'count' in result

    def test_run_diagnostic_with_no_data(self):
        """Test diagnostic run with empty dataset."""
        data = {
            'misorientation_angle': [],
            'sigma_value': []
        }

        result = run_collinearity_diagnostic(data)

        assert result['status'] == 'unavailable'
        assert result['count'] == 0


class TestSaveReport:
    """Tests for report saving functionality."""

    def test_save_report_creates_file(self):
        """Test that save_report creates the expected file."""
        report = {
            'status': 'computed',
            'mi_score': 0.85,
            'interpretation': 'Strong dependency detected'
        }
        output_path = Path(tempfile.mkdtemp()) / 'test_report.json'

        save_report(report, str(output_path))

        assert output_path.exists()
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        assert loaded == report

    def test_save_report_creates_directory(self):
        """Test that save_report creates parent directories if needed."""
        report = {'test': 'value'}
        output_path = Path(tempfile.mkdtemp()) / 'subdir' / 'nested' / 'report.json'

        save_report(report, str(output_path))

        assert output_path.exists()

    def test_save_report_invalid_json(self):
        """Test save_report with non-serializable data."""
        report = {'value': lambda x: x}  # Lambda is not JSON serializable
        output_path = Path(tempfile.mkdtemp()) / 'bad_report.json'

        # Should raise TypeError for non-serializable object
        with pytest.raises(TypeError):
            save_report(report, str(output_path))


class TestIntegration:
    """Integration tests for the diagnostics module."""

    def test_full_diagnostic_workflow(self):
        """Test the complete workflow from data to saved report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'collinearity_report.json'

            # Create realistic mock data
            np.random.seed(42)
            n_samples = 100
            misorientation = np.random.uniform(0, 90, n_samples)
            # Sigma is derived from misorientation (simplified relationship for test)
            sigma = np.round(1 / np.sin(np.radians(misorientation / 2))) + 1

            data = {
                'misorientation_angle': misorientation.tolist(),
                'sigma_value': sigma.tolist()
            }

            # Run diagnostic
            result = run_collinearity_diagnostic(data)
            save_report(result, str(output_path))

            # Verify output
            assert output_path.exists()
            with open(output_path, 'r') as f:
                saved_report = json.load(f)

            assert saved_report['status'] == 'computed'
            assert 'mi_score' in saved_report
            assert saved_report['mi_score'] > 0  # Should detect dependency

    def test_diagnostic_handles_mixed_nan(self):
        """Test diagnostic with mixed valid and NaN values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'mixed_report.json'

            data = {
                'misorientation_angle': [36.87, np.nan, 45.0, np.nan, 60.0],
                'sigma_value': [3.0, 5.0, np.nan, 7.0, np.nan]
            }

            result = run_collinearity_diagnostic(data)
            save_report(result, str(output_path))

            assert output_path.exists()
            with open(output_path, 'r') as f:
                saved_report = json.load(f)

            # Should handle partial data or report unavailability
            assert 'status' in saved_report