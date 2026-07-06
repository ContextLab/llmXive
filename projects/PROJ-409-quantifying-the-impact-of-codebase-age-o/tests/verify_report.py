"""
Unit tests for the report verification logic (T024.1).

This module programmatically asserts that the report JSON keys exist
and values are numeric/boolean as expected.
"""
import json
import tempfile
from pathlib import Path
import unittest

# Add project root to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.analysis.verify_report import (
    validate_required_keys,
    validate_numeric_values,
    validate_boolean_values,
    validate_significance_logic,
    validate_interpretation
)

class TestReportValidation(unittest.TestCase):
    """Test cases for report validation functions."""

    def setUp(self):
        """Create a valid sample report for testing."""
        self.valid_report = {
            "spearman_correlation_age_perplexity": 0.15,
            "spearman_correlation_age_correctness": -0.08,
            "p_value_age_perplexity": 0.12,
            "p_value_age_correctness": 0.45,
            "significant_age_perplexity": False,
            "significant_age_correctness": False,
            "interpretation": "No significant correlation found between codebase age and LLM metrics.",
            "methodology": "Spearman rank correlation with covariate control.",
            "data_summary": {"n": 850, "repos": 4}
        }

    def test_validate_required_keys_pass(self):
        """Test that a valid report passes required keys check."""
        passed, missing = validate_required_keys(self.valid_report)
        self.assertTrue(passed)
        self.assertEqual(missing, [])

    def test_validate_required_keys_fail(self):
        """Test that a report with missing keys fails."""
        incomplete_report = {k: v for k, v in self.valid_report.items() if k != "interpretation"}
        passed, missing = validate_required_keys(incomplete_report)
        self.assertFalse(passed)
        self.assertIn("interpretation", missing)

    def test_validate_numeric_values_pass(self):
        """Test that valid numeric values pass."""
        passed, errors = validate_numeric_values(self.valid_report)
        self.assertTrue(passed)
        self.assertEqual(errors, [])

    def test_validate_numeric_values_fail_type(self):
        """Test that non-numeric values fail."""
        bad_report = self.valid_report.copy()
        bad_report["spearman_correlation_age_perplexity"] = "not a number"
        passed, errors = validate_numeric_values(bad_report)
        self.assertFalse(passed)
        self.assertGreater(len(errors), 0)

    def test_validate_numeric_values_fail_range(self):
        """Test that p-values outside [0, 1] fail."""
        bad_report = self.valid_report.copy()
        bad_report["p_value_age_perplexity"] = 1.5
        passed, errors = validate_numeric_values(bad_report)
        self.assertFalse(passed)
        self.assertGreater(len(errors), 0)

    def test_validate_boolean_values_pass(self):
        """Test that valid boolean values pass."""
        passed, errors = validate_boolean_values(self.valid_report)
        self.assertTrue(passed)
        self.assertEqual(errors, [])

    def test_validate_boolean_values_fail(self):
        """Test that non-boolean values fail."""
        bad_report = self.valid_report.copy()
        bad_report["significant_age_perplexity"] = "true"
        passed, errors = validate_boolean_values(bad_report)
        self.assertFalse(passed)
        self.assertGreater(len(errors), 0)

    def test_validate_significance_logic_pass_false(self):
        """Test that significance=False when p >= 0.05 passes."""
        passed, errors = validate_significance_logic(self.valid_report)
        self.assertTrue(passed)
        self.assertEqual(errors, [])

    def test_validate_significance_logic_pass_true(self):
        """Test that significance=True when p < 0.05 passes."""
        report = self.valid_report.copy()
        report["p_value_age_perplexity"] = 0.03
        report["significant_age_perplexity"] = True
        passed, errors = validate_significance_logic(report)
        self.assertTrue(passed)
        self.assertEqual(errors, [])

    def test_validate_significance_logic_fail(self):
        """Test that inconsistent significance logic fails."""
        report = self.valid_report.copy()
        report["p_value_age_perplexity"] = 0.03  # < 0.05
        report["significant_age_perplexity"] = False  # But flag says False
        passed, errors = validate_significance_logic(report)
        self.assertFalse(passed)
        self.assertGreater(len(errors), 0)

    def test_validate_interpretation_pass(self):
        """Test that a valid interpretation passes."""
        passed, errors = validate_interpretation(self.valid_report)
        self.assertTrue(passed)
        self.assertEqual(errors, [])

    def test_validate_interpretation_empty(self):
        """Test that empty interpretation fails."""
        report = self.valid_report.copy()
        report["interpretation"] = ""
        passed, errors = validate_interpretation(report)
        self.assertFalse(passed)
        self.assertGreater(len(errors), 0)

if __name__ == "__main__":
    unittest.main()