import json
import os
import tempfile
from pathlib import Path

import unittest

# Import the function we just implemented
from src.report.generate import generate_robustness_report


class TestGenerateReport(unittest.TestCase):
    """Basic sanity checks for the robustness‑report generation."""

    def setUp(self):
        # Create a temporary directory to hold input / output files
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.input_path = self.tmp_dir / "robustness_input.json"
        self.output_path = self.tmp_dir / "robustness_output.json"

        # Example data with two modalities (visual & auditory)
        self.sample_data = {
            "results": [
                {"modality": "visual", "p_value": 0.04, "correlation": 0.22},
                {"modality": "auditory", "p_value": 0.07, "correlation": 0.18},
            ]
        }

        with self.input_path.open("w", encoding="utf-8") as f:
            json.dump(self.sample_data, f, indent=2)

    def test_bonferroni_correction(self):
        """Bonferroni should multiply each p‑value by the number of tests (2)."""
        generate_robustness_report(
            input_path=self.input_path,
            output_path=self.output_path,
            correction_method="bonferroni",
        )

        with self.output_path.open("r", encoding="utf-8") as f:
            out = json.load(f)

        self.assertIn("results", out)
        self.assertEqual(len(out["results"]), 2)

        # Expected corrected values: min(0.04*2,1)=0.08, min(0.07*2,1)=0.14
        corrected = [r["corrected_p_value"] for r in out["results"]]
        self.assertAlmostEqual(corrected[0], 0.08)
        self.assertAlmostEqual(corrected[1], 0.14)

    def test_fdr_correction(self):
        """Benjamini‑Hochberg should produce monotonic adjusted p‑values."""
        generate_robustness_report(
            input_path=self.input_path,
            output_path=self.output_path,
            correction_method="fdr",
        )

        with self.output_path.open("r", encoding="utf-8") as f:
            out = json.load(f)

        corrected = [r["corrected_p_value"] for r in out["results"]]
        # With two tests, the FDR adjusted values are:
        # rank 1 (p=0.04): 0.04*2/1 = 0.08
        # rank 2 (p=0.07): max(0.07*2/2, previous) = max(0.07, 0.08) = 0.08
        self.assertAlmostEqual(corrected[0], 0.08)
        self.assertAlmostEqual(corrected[1], 0.08)


if __name__ == "__main__":
    unittest.main()
