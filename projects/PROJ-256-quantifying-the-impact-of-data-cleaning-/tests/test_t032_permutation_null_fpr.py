"""
Simple integration test for T032 – ensures that the permutation null FPR
script runs without error and produces the expected JSON artifact.
"""
import os
import json
import unittest
import logging

from t032_permutation_null_fpr import main as t032_main
from config import get_config

class TestPermutationNullFPR(unittest.TestCase):
    def setUp(self):
        # Ensure the processed directory exists and contains at least one tiny dataset.
        self.config = get_config()
        self.processed_dir = self.config.get("PROCESSED_DATA_PATH", "data/processed")
        os.makedirs(self.processed_dir, exist_ok=True)

        # Create a minimal synthetic dataset if none exist.
        existing_csvs = [f for f in os.listdir(self.processed_dir) if f.endswith(".csv")]
        if not existing_csvs:
            import pandas as pd
            df = pd.DataFrame({
                "feature1": [1, 2, 3, 4],
                "feature2": [5, 6, 7, 8],
                "target":    [0, 1, 0, 1],
            })
            df.to_csv(os.path.join(self.processed_dir, "synthetic_test.csv"), index=False)

    def test_null_fpr_generation(self):
        # Run the script
        t032_main()

        # Verify output file exists and contains a dict with numeric values
        output_path = os.path.join(
            self.processed_dir,
            "null_fpr_metrics.json"
        )
        self.assertTrue(os.path.isfile(output_path), "null_fpr_metrics.json was not created")

        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIsInstance(data, dict)
        for key, val in data.items():
            self.assertIsInstance(key, str)
            self.assertIsInstance(val, (int, float))

if __name__ == "__main__":
    # Configure root logger for test output visibility
    logging.basicConfig(level=logging.INFO)
    unittest.main()