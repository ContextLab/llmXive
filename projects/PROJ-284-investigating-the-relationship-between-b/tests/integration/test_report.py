"""
Integration tests for report generation.
"""
import os
import tempfile
from pathlib import Path
import unittest
import pandas as pd

from code.report.generate import generate_report, load_template, generate_conclusion


class TestReportGeneration(unittest.TestCase):
    """Integration tests for the report generator."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_report = Path(self.temp_dir) / "test_report.md"

        # Create dummy data files
        self.correlation_file = Path(self.temp_dir) / "correlation_results.csv"
        self.power_file = Path(self.temp_dir) / "power_analysis.csv"
        self.metrics_file = Path(self.temp_dir) / "full_metrics.csv"

        # Dummy correlation results
        corr_data = {
            "metric_name": ["Modularity", "Global_Efficiency", "Participation_Coeff"],
            "r": [0.32, -0.41, 0.15],
            "p": [0.008, 0.001, 0.25],
            "q": [0.024, 0.003, 0.45],
            "significant": [True, True, False],
            "covariate_controlled": [True, True, True]
        }
        pd.DataFrame(corr_data).to_csv(self.correlation_file, index=False)

        # Dummy power analysis
        power_data = {
            "metric": ["Modularity", "Global_Efficiency"],
            "n": [100, 100],
            "detectable_r": [0.25, 0.25],
            "power": [0.80, 0.80]
        }
        pd.DataFrame(power_data).to_csv(self.power_file, index=False)

        # Dummy metrics
        metrics_data = {
            "subject_id": list(range(10)),
            "modularity": [0.3 + i*0.01 for i in range(10)],
            "global_efficiency": [0.4 - i*0.01 for i in range(10)],
            "motor_score": [50 + i*2 for i in range(10)]
        }
        pd.DataFrame(metrics_data).to_csv(self.metrics_file, index=False)

    def tearDown(self):
        """Clean up test files."""
        if self.output_report.exists():
            self.output_report.unlink()
        for f in Path(self.temp_dir).glob("*"):
            f.unlink()
        os.rmdir(self.temp_dir)

    def test_report_generates_markdown_with_all_sections(self):
        """
        Test that the report generator produces a Markdown file containing
        all required sections: correlation table, power analysis, plots, limitations.
        """
        # Generate report
        result_path = generate_report(
            correlation_path=self.correlation_file,
            power_path=self.power_file,
            metrics_path=self.metrics_file,
            output_path=self.output_report
        )

        # Verify file exists
        self.assertTrue(result_path.exists(), "Report file was not created")

        # Read content
        content = result_path.read_text()

        # Verify required sections exist
        required_sections = [
            "# Correlation Analysis Results",
            "# Power Analysis",
            "# Limitations",
            "associational relationship",  # Or "correlational evidence"
            "Motor Task Performance is a proxy"
        ]

        for section in required_sections:
            self.assertIn(
                section, content,
                f"Required section/phrase '{section}' not found in report"
            )

        # Verify table formatting
        self.assertIn("Metric", content)
        self.assertIn("r", content)
        self.assertIn("p", content)
        self.assertIn("q", content)

    def test_conclusion_phrasing(self):
        """Test that the conclusion uses the required phrasing."""
        # Create minimal dummy data
        corr_data = {
            "metric_name": ["Test"],
            "r": [0.3],
            "p": [0.02],
            "q": [0.05],
            "significant": [True],
            "covariate_controlled": [True]
        }
        pd.DataFrame(corr_data).to_csv(self.correlation_file, index=False)

        pd.DataFrame({"metric": ["Test"], "n": [50], "detectable_r": [0.3], "power": [0.8]}).to_csv(self.power_file, index=False)
        pd.DataFrame({"subject_id": [1], "Test": [0.3], "motor_score": [50]}).to_csv(self.metrics_file, index=False)

        generate_report(
            correlation_path=self.correlation_file,
            power_path=self.power_file,
            metrics_path=self.metrics_file,
            output_path=self.output_report
        )

        content = self.output_report.read_text()

        # Check for alternative phrasings
        has_phrase = (
            "associational relationship" in content.lower() or
            "correlational evidence" in content.lower()
        )
        self.assertTrue(
            has_phrase,
            "Report conclusion must contain 'associational relationship' or 'correlational evidence'"
        )

    def test_limitation_statement(self):
        """Test that the limitation statement is present."""
        # Generate report with dummy data
        corr_data = {
            "metric_name": ["Test"],
            "r": [0.3],
            "p": [0.02],
            "q": [0.05],
            "significant": [True],
            "covariate_controlled": [True]
        }
        pd.DataFrame(corr_data).to_csv(self.correlation_file, index=False)
        pd.DataFrame({"metric": ["Test"], "n": [50], "detectable_r": [0.3], "power": [0.8]}).to_csv(self.power_file, index=False)
        pd.DataFrame({"subject_id": [1], "Test": [0.3], "motor_score": [50]}).to_csv(self.metrics_file, index=False)

        generate_report(
            correlation_path=self.correlation_file,
            power_path=self.power_file,
            metrics_path=self.metrics_file,
            output_path=self.output_report
        )

        content = self.output_report.read_text()

        self.assertIn(
            "Motor Task Performance is a proxy for proprioceptive accuracy",
            content,
            "Limitation statement about proxy measure not found"
        )


if __name__ == "__main__":
    unittest.main()