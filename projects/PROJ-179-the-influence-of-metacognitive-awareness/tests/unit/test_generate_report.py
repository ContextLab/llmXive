import json
import os
import unittest
from pathlib import Path

from src.report.generate import generate_robustness_report


class TestGenerateRobustnessReport(unittest.TestCase):
    """
    Basic unit tests for the robustness report generation logic.
    """

    def setUp(self):
        # Create a temporary directory for input / output files
        self.tmp_dir = Path("tmp_test_report")
        self.tmp_dir.mkdir(exist_ok=True)
        self.input_file = self.tmp_dir / "raw.json"
        self.output_file = self.tmp_dir / "corrected.json"

        # Sample raw results – two modalities with simple p‑values
        self.raw_results = [
            {"modality": "visual", "correlation": 0.25, "p_value": 0.04},
            {"modality": "auditory", "correlation": -0.10, "p_value": 0.20},
        ]
        with open(self.input_file, "w", encoding="utf-8") as f:
            json.dump(self.raw_results, f, indent=2)

    def tearDown(self):
        # Clean up temporary files
        for p in self.tmp_dir.iterdir():
            p.unlink()
        self.tmp_dir.rmdir()

    def test_bonferroni_correction(self):
        generate_robustness_report(self.input_file, self.output_file, method="bonferroni")
        with open(self.output_file, "r", encoding="utf-8") as f:
            corrected = json.load(f)
        # Bonferroni multiplies by number of tests (2)
        self.assertAlmostEqual(corrected[0]["corrected_p_value"], min(0.04 * 2, 1.0))
        self.assertAlmostEqual(corrected[1]["corrected_p_value"], min(0.20 * 2, 1.0))
        self.assertEqual(corrected[0]["correction_method"], "bonferroni")

    def test_bh_correction(self):
        generate_robustness_report(self.input_file, self.output_file, method="bh")
        with open(self.output_file, "r", encoding="utf-8") as f:
            corrected = json.load(f)
        # For two p‑values 0.04 and 0.20, BH yields 0.08 and 0.20 respectively
        self.assertAlmostEqual(corrected[0]["corrected_p_value"], 0.08)
        self.assertAlmostEqual(corrected[1]["corrected_p_value"], 0.20)
        self.assertEqual(corrected[1]["correction_method"], "bh")


if __name__ == "__main__":
    unittest.main()
