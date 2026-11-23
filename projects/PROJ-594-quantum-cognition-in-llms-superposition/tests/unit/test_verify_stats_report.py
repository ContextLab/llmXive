"""
Unit tests for verify_stats_report.py functionality.

Tests the verification logic for T032 without requiring actual execution.
"""
import os
import sys
import json
import tempfile
import unittest

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.analysis.verify_stats_report import verify_report, REQUIRED_FIELDS


class TestVerifyStatsReport(unittest.TestCase):
    """Test cases for stats report verification."""

    def test_all_fields_present(self):
        """Test that a valid report with all fields passes verification."""
        valid_report = {
            'p_value': 0.03,
            't_statistic': 2.15,
            'cohens_d': 0.45,
            'ci_95_lower': 0.01,
            'ci_95_upper': 0.15,
            'method': 'paired_ttest',
            'n_seeds': 5
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(valid_report, f)
            temp_path = f.name

        try:
            result = verify_report(temp_path)
            self.assertTrue(result)
        finally:
            os.unlink(temp_path)

    def test_missing_p_value(self):
        """Test that missing p-value fails verification."""
        invalid_report = {
            't_statistic': 2.15,
            'cohens_d': 0.45,
            'ci_95_lower': 0.01,
            'ci_95_upper': 0.15
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_report, f)
            temp_path = f.name

        try:
            result = verify_report(temp_path)
            self.assertFalse(result)
        finally:
            os.unlink(temp_path)

    def test_missing_cohens_d(self):
        """Test that missing Cohen's d fails verification."""
        invalid_report = {
            'p_value': 0.03,
            't_statistic': 2.15,
            'ci_95_lower': 0.01,
            'ci_95_upper': 0.15
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_report, f)
            temp_path = f.name

        try:
            result = verify_report(temp_path)
            self.assertFalse(result)
        finally:
            os.unlink(temp_path)

    def test_invalid_p_value_range(self):
        """Test that p-value outside [0, 1] fails verification."""
        invalid_report = {
            'p_value': 1.5,  # Out of range
            't_statistic': 2.15,
            'cohens_d': 0.45,
            'ci_95_lower': 0.01,
            'ci_95_upper': 0.15
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_report, f)
            temp_path = f.name

        try:
            result = verify_report(temp_path)
            self.assertFalse(result)
        finally:
            os.unlink(temp_path)

    def test_non_numeric_p_value(self):
        """Test that non-numeric p-value fails verification."""
        invalid_report = {
            'p_value': "not_a_number",
            't_statistic': 2.15,
            'cohens_d': 0.45,
            'ci_95_lower': 0.01,
            'ci_95_upper': 0.15
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_report, f)
            temp_path = f.name

        try:
            result = verify_report(temp_path)
            self.assertFalse(result)
        finally:
            os.unlink(temp_path)

    def test_file_not_found(self):
        """Test that missing file fails verification."""
        result = verify_report('/nonexistent/path/stats_report.json')
        self.assertFalse(result)

    def test_invalid_json(self):
        """Test that invalid JSON fails verification."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('not valid json {')
            temp_path = f.name

        try:
            result = verify_report(temp_path)
            self.assertFalse(result)
        finally:
            os.unlink(temp_path)

    def test_required_fields_structure(self):
        """Test that REQUIRED_FIELDS dict has expected structure."""
        self.assertIn('p_value', REQUIRED_FIELDS)
        self.assertIn('t_statistic', REQUIRED_FIELDS)
        self.assertIn('cohens_d', REQUIRED_FIELDS)
        self.assertIn('ci_95_lower', REQUIRED_FIELDS)
        self.assertIn('ci_95_upper', REQUIRED_FIELDS)

        self.assertEqual(REQUIRED_FIELDS['p_value'], 'p-value')
        self.assertEqual(REQUIRED_FIELDS['t_statistic'], 't-statistic')
        self.assertEqual(REQUIRED_FIELDS['cohens_d'], "Cohen's d")


if __name__ == '__main__':
    unittest.main()