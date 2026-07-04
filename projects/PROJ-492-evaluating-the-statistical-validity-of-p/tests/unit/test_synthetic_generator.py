"""
Unit tests for the synthetic dataset generator (T026).
"""
import csv
import json
import os
import tempfile
from pathlib import Path
import unittest

# Add code directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from src.audit.synthetic import (
    generate_synthetic_dataset,
    verify_outcome_types,
    write_csv_output,
    write_json_output,
    generate_binary_outcome,
    generate_continuous_outcome
)

class TestSyntheticGenerator(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.csv_path = Path(self.temp_dir) / "test.csv"
        self.json_path = Path(self.temp_dir) / "test.json"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generate_binary_outcome_structure(self):
        """Test that binary outcome generation returns expected keys."""
        data = generate_binary_outcome(1000, 1000, 0.1, 0.05, False)
        required_keys = [
            "n_control", "n_treatment", "successes_control", "successes_treatment",
            "rate_control", "rate_treatment", "reported_p_value", "true_p_value",
            "observed_effect", "true_effect", "outcome_type"
        ]
        for key in required_keys:
            self.assertIn(key, data)
        self.assertEqual(data["outcome_type"], "binary")

    def test_generate_continuous_outcome_structure(self):
        """Test that continuous outcome generation returns expected keys."""
        data = generate_continuous_outcome(1000, 1000, 50.0, 5.0, 10.0, False)
        required_keys = [
            "n_control", "n_treatment", "mean_control", "mean_treatment",
            "std_control", "std_treatment", "reported_p_value", "true_p_value",
            "observed_effect", "true_effect", "outcome_type"
        ]
        for key in required_keys:
            self.assertIn(key, data)
        self.assertEqual(data["outcome_type"], "continuous")

    def test_full_generation_and_verification(self):
        """Test full dataset generation, writing, and verification."""
        records, metadata = generate_synthetic_dataset(count=100, seed=42)
        
        # Check record count
        self.assertEqual(len(records), 100)
        
        # Check verification
        self.assertTrue(verify_outcome_types(records))
        
        # Check metadata
        self.assertIn("binary_count", metadata)
        self.assertIn("continuous_count", metadata)
        self.assertGreater(metadata["binary_count"] + metadata["continuous_count"], 0)

    def test_csv_output_writing(self):
        """Test that CSV output is written correctly."""
        records, _ = generate_synthetic_dataset(count=50, seed=42)
        write_csv_output(records, self.csv_path)
        
        self.assertTrue(self.csv_path.exists())
        
        with open(self.csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 50)
            # Check header
            self.assertIn("outcome_type", reader.fieldnames)

    def test_json_output_writing(self):
        """Test that JSON output is written correctly."""
        _, metadata = generate_synthetic_dataset(count=50, seed=42)
        write_json_output(metadata, self.json_path)
        
        self.assertTrue(self.json_path.exists())
        
        with open(self.json_path, 'r') as f:
            loaded_meta = json.load(f)
            self.assertEqual(loaded_meta["total_records"], 50)
            self.assertIn("generation_timestamp", loaded_meta)

    def test_both_outcome_types_present_in_large_set(self):
        """Ensure large dataset contains both types (constraint-preservation)."""
        records, _ = generate_synthetic_dataset(count=1000, seed=42)
        types = set(r["outcome_type"] for r in records)
        self.assertIn("binary", types)
        self.assertIn("continuous", types)
        self.assertEqual(len(types), 2)

if __name__ == "__main__":
    unittest.main()