"""
Unit tests for report structure validation (Task T025).

This module validates that the generated R-Markdown report contains all
required sections as specified in the project requirements:
- Descriptive statistics
- ANCOVA results
- Effect sizes (Cohen's d)
- Power analysis (G*Power summary)
- Sensitivity analysis table
- Reliability metrics (Cronbach's alpha)
- Data exclusion summary

The test verifies the existence of these sections by parsing the
generated HTML/Markdown report.
"""
import os
import re
import unittest
from pathlib import Path


class TestReportStructure(unittest.TestCase):
    """Test suite for validating report structure."""

    # Paths relative to project root
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    REPORT_PATH = PROJECT_ROOT / "reports" / "chronotype_moral_analysis.html"
    SENSITIVITY_CSV = PROJECT_ROOT / "data" / "derived" / "sensitivity_sweep.csv"
    RELIABILITY_CSV = PROJECT_ROOT / "data" / "derived" / "reliability_metrics.csv"
    EXCLUSIONS_LOG = PROJECT_ROOT / "data" / "derived" / "exclusions.log"

    def setUp(self):
        """Set up test fixtures."""
        self.report_path = self.REPORT_PATH
        self.required_sections = [
            r"(?i)Descriptive\s+Statistics",
            r"(?i)ANCOVA\s+Results",
            r"(?i)Effect\s+Sizes",
            r"(?i)Power\s+Analysis",
            r"(?i)Sensitivity\s+Analysis",
            r"(?i)Reliability\s+Metrics",
            r"(?i)Data\s+Exclusion\s+Summary"
        ]

    def test_report_file_exists(self):
        """Verify that the report file exists."""
        self.assertTrue(
            self.report_path.exists(),
            f"Report file not found at {self.report_path}. "
            "Ensure code/04_report.Rmd has been rendered."
        )

    def test_report_contains_required_sections(self):
        """Verify that the report contains all required sections."""
        if not self.report_path.exists():
            self.skipTest("Report file does not exist; skipping section check.")

        with open(self.report_path, "r", encoding="utf-8") as f:
            content = f.read()

        missing_sections = []
        for pattern in self.required_sections:
            if not re.search(pattern, content):
                missing_sections.append(pattern)

        self.assertEqual(
            len(missing_sections), 0,
            f"Report is missing the following sections:\n"
            + "\n".join(missing_sections)
        )

    def test_sensitivity_table_has_required_columns(self):
        """Verify that sensitivity_sweep.csv has required columns."""
        if not self.SENSITIVITY_CSV.exists():
            self.skipTest("Sensitivity sweep CSV not found; skipping column check.")

        # Read first line to check headers
        with open(self.SENSITIVITY_CSV, "r", encoding="utf-8") as f:
            header_line = f.readline().strip()

        required_cols = ["subscale", "alpha_threshold", "p_value", "significant"]
        cols = [c.strip() for c in header_line.split(",")]

        missing_cols = [c for c in required_cols if c not in cols]
        self.assertEqual(
            len(missing_cols), 0,
            f"Sensitivity sweep CSV missing columns: {missing_cols}"
        )

    def test_sensitivity_table_has_multiple_thresholds(self):
        """Verify that sensitivity table includes at least three alpha thresholds."""
        if not self.SENSITIVITY_CSV.exists():
            self.skipTest("Sensitivity sweep CSV not found; skipping threshold count check.")

        import pandas as pd
        df = pd.read_csv(self.SENSITIVITY_CSV)

        unique_thresholds = df["alpha_threshold"].unique()
        self.assertGreaterEqual(
            len(unique_thresholds), 3,
            f"Sensitivity table must include at least 3 alpha thresholds. "
            f"Found: {len(unique_thresholds)}"
        )

    def test_reliability_metrics_exists_and_valid(self):
        """Verify that reliability_metrics.csv exists and has valid alpha values."""
        if not self.RELIABILITY_CSV.exists():
            self.skipTest("Reliability metrics CSV not found; skipping validation.")

        import pandas as pd
        df = pd.read_csv(self.RELIABILITY_CSV)

        required_cols = ["subscale", "cronbach_alpha", "n_items"]
        missing_cols = [c for c in required_cols if c not in df.columns]
        self.assertEqual(
            len(missing_cols), 0,
            f"Reliability metrics CSV missing columns: {missing_cols}"
        )

        # Check that alpha values are between 0 and 1
        self.assertTrue(
            all((df["cronbach_alpha"] >= 0) & (df["cronbach_alpha"] <= 1)),
            "Cronbach's alpha values must be between 0 and 1."
        )

    def test_exclusions_log_exists(self):
        """Verify that exclusions.log exists."""
        self.assertTrue(
            self.EXCLUSIONS_LOG.exists(),
            f"Exclusions log not found at {self.EXCLUSIONS_LOG}. "
            "Ensure T012.5 has been run to generate this file."
        )


if __name__ == "__main__":
    unittest.main()
