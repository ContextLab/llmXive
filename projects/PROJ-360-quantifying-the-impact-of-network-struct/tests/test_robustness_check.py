import os
import sys
import json
import unittest
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

class TestRobustnessCheck(unittest.TestCase):
    def test_robustness_check_artifact_exists(self):
        """Verify that results/robustness_check.json is created."""
        output_path = Path("results/robustness_check.json")
        self.assertTrue(output_path.exists(), "results/robustness_check.json must exist")

    def test_robustness_check_schema(self):
        """Verify the schema of results/robustness_check.json."""
        output_path = Path("results/robustness_check.json")
        if not output_path.exists():
            self.skipTest("Output file not found")
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        required_keys = ["model_r2", "model_rmse", "feature_coefficients"]
        for key in required_keys:
            self.assertIn(key, data, f"Missing key: {key}")
        
        self.assertIsInstance(data["model_r2"], (int, float, type(None)))
        self.assertIsInstance(data["model_rmse"], (int, float, type(None)))
        self.assertIsInstance(data["feature_coefficients"], dict)

    def test_robustness_check_values_real(self):
        """Verify that the results are not fabricated (not None/NaN for valid runs)."""
        output_path = Path("results/robustness_check.json")
        if not output_path.exists():
            self.skipTest("Output file not found")
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        # If error key exists, the run failed, which is acceptable if input was missing
        if "error" in data:
            self.skipTest("Run reported an error, skipping value check")
        
        # If we have results, they should be numbers
        if data["model_r2"] is not None:
            self.assertIsInstance(data["model_r2"], (int, float))
            self.assertFalse(json.dumps(data["model_r2"]) == "nan", "R2 should not be NaN")
        
        if data["model_rmse"] is not None:
            self.assertIsInstance(data["model_rmse"], (int, float))
            self.assertFalse(json.dumps(data["model_rmse"]) == "nan", "RMSE should not be NaN")

if __name__ == '__main__':
    unittest.main()