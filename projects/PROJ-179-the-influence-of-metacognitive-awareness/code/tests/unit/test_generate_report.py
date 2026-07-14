"""
Unit tests for the ``src.report.generate`` module.

The tests verify that the report generation function creates a JSON file with the
expected structure even when the upstream result files are missing or empty.
"""

import json
import os
import unittest
from pathlib import Path

# Import the function under test.
from src.report.generate import generate_regression_analysis_report

class TestGenerateReport(unittest.TestCase):
    """Test the behaviour of ``generate_regression_analysis_report``."""

    def setUp(self):
        """Create a temporary directory structure for the test."""
        self.base_dir = Path("tmp_test_report")
        self.base_dir.mkdir(exist_ok=True)
        # Override the default paths by feeding explicit arguments.
        self.regression_path = self.base_dir / "regression_results.json"
        self.diagnostics_path = self.base_dir / "diagnostics.json"
        self.output_path = self.base_dir / "regression_analysis.json"

    def tearDown(self):
        """Remove the temporary files created during the test."""
        for path in self.base_dir.rglob("*"):
            path.unlink()
        self.base_dir.rmdir()

    def _write_json(self, path: Path, payload: dict):
        """Helper to write a JSON payload to ``path``."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f)

    def test_report_created_with_full_input(self):
        """When both regression and diagnostics files exist, the merged report
        contains the combined information."""
        regression_payload = {
            "coefficients": [
                {
                    "name": "type2_auc",
                    "estimate": 0.62,
                    "std_error": 0.07,
                    "t_stat": 8.86,
                    "p_value": 0.0001,
                },
                {
                    "name": "age",
                    "estimate": -0.02,
                    "std_error": 0.01,
                    "t_stat": -2.00,
                    "p_value": 0.045,
                },
            ]
        }
        diagnostics_payload = {
            "normality_passed": True,
            "homoscedasticity_passed": True,
            "collinearity_flagged": False,
        }

        self._write_json(self.regression_path, regression_payload)
        self._write_json(self.diagnostics_path, diagnostics_payload)

        generate_regression_analysis_report(
            regression_path=self.regression_path,
            diagnostics_path=self.diagnostics_path,
            output_path=self.output_path,
        )

        # Verify output file exists and contains the merged structure.
        self.assertTrue(self.output_path.is_file())
        with self.output_path.open("r", encoding="utf-8") as f:
            output = json.load(f)

        self.assertIn("coefficients", output)
        self.assertEqual(output["coefficients"], regression_payload["coefficients"])
        self.assertIn("diagnostics", output)
        self.assertEqual(output["diagnostics"], diagnostics_payload)

    def test_report_created_when_inputs_missing(self):
        """If upstream files are missing, the function should still create a
        valid (but empty) report rather than raising."""
        # Do NOT create any upstream files.
        generate_regression_analysis_report(
            regression_path=self.regression_path,
            diagnostics_path=self.diagnostics_path,
            output_path=self.output_path,
        )

        self.assertTrue(self.output_path.is_file())
        with self.output_path.open("r", encoding="utf-8") as f:
            output = json.load(f)

        # Expect empty structures.
        self.assertEqual(output.get("coefficients", []), [])
        self.assertIn("diagnostics", output)
        self.assertFalse(output["diagnostics"].get("normality_passed", True))
        self.assertFalse(output["diagnostics"].get("homoscedasticity_passed", True))
        self.assertFalse(output["diagnostics"].get("collinearity_flagged", True))

if __name__ == "__main__":
    unittest.main()
