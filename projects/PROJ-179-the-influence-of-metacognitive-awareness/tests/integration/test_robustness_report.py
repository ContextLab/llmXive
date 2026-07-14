import json
import unittest
from pathlib import Path

from src.report.generate import main as generate_main

class TestRobustnessReportIntegration(unittest.TestCase):
    """Integration test that runs the full report generator and checks output."""

    def setUp(self):
        # Prepare a minimal robustness results file
        self.results_path = Path("data/results/robustness_analysis.json")
        self.results_path.parent.mkdir(parents=True, exist_ok=True)
        sample = [
            {"modality": "visual", "correlation_coefficient": 0.15, "p_value": 0.05},
            {"modality": "auditory", "correlation_coefficient": -0.12, "p_value": 0.30},
        ]
        self.results_path.write_text(json.dumps(sample, indent=2))

    def tearDown(self):
        # Clean up after test
        if self.results_path.is_file():
            self.results_path.unlink()

    def test_generate_robustness_report_integration(self):
        # Run the full report generator (which includes robustness correction)
        generate_main()

        # Verify that corrected p‑values have been added
        data = json.loads(self.results_path.read_text())
        self.assertIn("corrected_p_value", data[0])
        self.assertIn("corrected_p_value", data[1])

if __name__ == "__main__":
    unittest.main()