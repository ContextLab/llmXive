import json
import os
import unittest
from pathlib import Path

from src.report.generate import generate_robustness_report

class TestGenerateRobustnessReport(unittest.TestCase):
    """Simple unit tests for the robustness correction logic."""

    def setUp(self):
        # Create a temporary JSON file with known p‑values
        self.tmp_path = Path("data/results/_tmp_robustness.json")
        self.tmp_path.parent.mkdir(parents=True, exist_ok=True)
        sample = [
            {"modality": "visual", "correlation_coefficient": 0.2, "p_value": 0.04},
            {"modality": "auditory", "correlation_coefficient": -0.1, "p_value": 0.20},
            {"modality": "visual", "correlation_coefficient": 0.35, "p_value": 0.01},
        ]
        self.tmp_path.write_text(json.dumps(sample, indent=2))

    def tearDown(self):
        # Clean up the temporary file
        if self.tmp_path.is_file():
            self.tmp_path.unlink()

    def test_bonferroni_correction(self):
        generate_robustness_report(
            input_path=str(self.tmp_path),
            method="bonferroni",
            output_path=str(self.tmp_path),
        )
        data = json.loads(self.tmp_path.read_text())
        # Bonferroni multiplies by m=3, capped at 1.0
        self.assertAlmostEqual(data[0]["corrected_p_value"], min(0.04 * 3, 1.0))
        self.assertAlmostEqual(data[1]["corrected_p_value"], min(0.20 * 3, 1.0))
        self.assertAlmostEqual(data[2]["corrected_p_value"], min(0.01 * 3, 1.0))

    def test_bh_correction(self):
        generate_robustness_report(
            input_path=str(self.tmp_path),
            method="bh",
            output_path=str(self.tmp_path),
        )
        data = json.loads(self.tmp_path.read_text())
        # Manual BH calculation for p-values [0.01,0.04,0.20]
        # ranks: 1->0.01, 2->0.04, 3->0.20
        # adjusted: 0.01*3/1=0.03, 0.04*3/2=0.06, 0.20*3/3=0.20
        # enforce monotonicity: [0.03,0.06,0.20]
        self.assertAlmostEqual(data[0]["corrected_p_value"], 0.03)
        self.assertAlmostEqual(data[1]["corrected_p_value"], 0.06)
        self.assertAlmostEqual(data[2]["corrected_p_value"], 0.20)

if __name__ == "__main__":
    unittest.main()