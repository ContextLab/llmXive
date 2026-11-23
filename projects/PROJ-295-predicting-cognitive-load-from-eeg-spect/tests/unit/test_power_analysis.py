"""
Unit tests for code/data/power_analysis.py
"""
import os
import sys
import json
import math
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from data.power_analysis import (
    calculate_minimum_n,
    load_verification_report,
    NON_CENTRAL_PARAM,
    TARGET_R2
)


class TestCalculateMinimumN(unittest.TestCase):
    """Tests for the minimum N calculation logic."""

    def test_standard_calculation(self):
        """Test standard calculation with known values."""
        # k=10, R2=0.2
        # N = 10 + (7.85 * 0.8) / 0.2 = 10 + 31.4 = 41.4 -> 42
        k = 10
        r2 = 0.2
        result = calculate_minimum_n(k, r2)
        expected = math.ceil(k + (NON_CENTRAL_PARAM * (1 - r2)) / r2)
        self.assertEqual(result, expected)

    def test_high_predictors(self):
        """Test with high number of predictors."""
        k = 64 * 2  # 128 predictors
        r2 = 0.2
        result = calculate_minimum_n(k, r2)
        # Should be significantly larger than k
        self.assertGreater(result, k)

    def test_invalid_r2(self):
        """Test that invalid R2 raises error."""
        with self.assertRaises(ValueError):
            calculate_minimum_n(10, 1.5)
        with self.assertRaises(ValueError):
            calculate_minimum_n(10, -0.1)

    def test_zero_r2(self):
        """Test that zero R2 raises error (division by zero)."""
        with self.assertRaises(ValueError):
            calculate_minimum_n(10, 0)


class TestLoadVerificationReport(unittest.TestCase):
    """Tests for loading the verification report."""

    def setUp(self):
        """Create a temporary directory and mock report."""
        self.temp_dir = tempfile.mkdtemp()
        self.report_path = os.path.join(self.temp_dir, 'verification_report.json')

    def tearDown(self):
        """Clean up temp directory."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_load_success(self):
        """Test loading a valid report."""
        data = {
            'status': 'success',
            'n_channels': 64,
            'message': 'OK'
        }
        with open(self.report_path, 'w') as f:
            json.dump(data, f)

        result = load_verification_report(self.report_path)
        self.assertEqual(result['n_channels'], 64)
        self.assertEqual(result['status'], 'success')

    def test_missing_file(self):
        """Test that missing file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            load_verification_report('/nonexistent/path.json')

    def test_missing_fields(self):
        """Test that missing required fields raises ValueError."""
        data = {'status': 'success'} # Missing n_channels
        with open(self.report_path, 'w') as f:
            json.dump(data, f)

        with self.assertRaises(ValueError):
            load_verification_report(self.report_path)

    def test_failed_status(self):
        """Test that failed status raises ValueError."""
        data = {
            'status': 'failed',
            'n_channels': 64
        }
        with open(self.report_path, 'w') as f:
            json.dump(data, f)

        with self.assertRaises(ValueError):
            load_verification_report(self.report_path)


if __name__ == '__main__':
    unittest.main()