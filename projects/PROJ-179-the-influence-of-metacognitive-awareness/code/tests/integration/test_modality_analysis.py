"""
Integration test for modality‑specific analysis (Task T025).

The test runs the full pipeline for both visual and auditory modalities
and checks that the resulting JSON file contains the expected keys.
"""

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

class TestModalityAnalysis(unittest.TestCase):
    """Run the robustness analysis and verify its output."""

    @classmethod
    def setUpClass(cls):
        # Ensure the project root is on the PYTHONPATH for imports.
        project_root = Path(__file__).resolve().parents[3]
        sys.path.insert(0, str(project_root))

        # Run the quick‑start pipeline which, among other things,
        # invokes the robustness analysis that writes the expected file.
        # The quick‑start command is defined in ``quickstart.md`` but we
        # replicate the essential steps here to keep the test self‑contained.
        #
        # 1. Download data
        subprocess.run(
            [sys.executable, "code/data/download.py"],
            check=True,
            cwd=str(project_root),
        )
        # 2. Validate data (T006) – this script creates a validation report.
        subprocess.run(
            [sys.executable, "code/data/validate_data.py"],
            check=True,
            cwd=str(project_root),
        )
        # 3. Preprocess (T012) – creates trial_data.csv
        subprocess.run(
            [sys.executable, "code/data/preprocess.py"],
            check=True,
            cwd=str(project_root),
        )
        # 4. Run the robustness analysis (T027)
        subprocess.run(
            [sys.executable, "code/src/analysis/robustness.py"],
            check=True,
            cwd=str(project_root),
        )

    def test_robustness_output_exists(self):
        """The robustness analysis must produce the declared JSON file."""
        project_root = Path(__file__).resolve().parents[3]
        result_path = (
            project_root
            / "data"
            / "results"
            / "robustness_analysis.json"
        )
        self.assertTrue(
            result_path.is_file(),
            f"Expected result file {result_path} was not created.",
        )
        # Verify the JSON structure contains the keys we expect.
        with result_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("visual", data, "Missing 'visual' entry in results.")
        self.assertIn("auditory", data, "Missing 'auditory' entry in results.")
        self.assertIn("correlation", data["visual"])
        self.assertIn("correlation", data["auditory"])

    def test_output_schema(self):
        """Ensure each modality entry contains the required fields."""
        project_root = Path(__file__).resolve().parents[3]
        result_path = (
            project_root
            / "data"
            / "results"
            / "robustness_analysis.json"
        )
        with result_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        for modality in ("visual", "auditory"):
            entry = data[modality]
            self.assertIn("correlation", entry)
            self.assertIn("ci_lower", entry)
            self.assertIn("ci_upper", entry)
            self.assertIn("p_value", entry)

if __name__ == "__main__":
    unittest.main()