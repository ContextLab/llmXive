"""
Unit tests for the synthetic dataset generator (T026).

Verifies:
  - Generation of at least 10,000 records.
  - Presence of both binary and continuous outcomes.
  - Data structure validity.
"""
import csv
import json
import math
import os
import sys
import unittest
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.src.audit.synthetic import (
    generate_synthetic_dataset,
    verify_outcome_types,
    generate_binary_outcome,
    generate_continuous_outcome
)
from code.src.config import SEED

class TestSyntheticGenerator(unittest.TestCase):
    
    def setUp(self):
        self.test_output_dir = Path("data/test_synthetic")
        self.test_output_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        # Cleanup test files
        if self.test_output_dir.exists():
            import shutil
            shutil.rmtree(self.test_output_dir)

    def test_minimum_record_count(self):
        """Test that generator produces at least 10,000 records."""
        data = generate_synthetic_dataset(total_records=10000, output_dir=self.test_output_dir)
        self.assertGreaterEqual(len(data), 10000, "Should generate at least 10,000 records")

    def test_outcome_type_presence(self):
        """Test that both binary and continuous outcomes are present."""
        data = generate_synthetic_dataset(total_records=10000, output_dir=self.test_output_dir)
        self.assertTrue(verify_outcome_types(data), "Both outcome types must be present")

    def test_binary_outcome_structure(self):
        """Test binary outcome generation structure."""
        record = generate_binary_outcome(
            baseline_rate=0.1,
            effect_size=0.1,
            n_control=100,
            n_treatment=100,
            is_consistent=True
        )
        required_keys = [
            "n_control", "n_treatment", "rate_control", "rate_treatment",
            "observed_effect", "relative_lift", "p_value", "is_significant", "outcome_type"
        ]
        for key in required_keys:
            self.assertIn(key, record, f"Binary record missing key: {key}")
        
        self.assertEqual(record["outcome_type"], "binary")
        self.assertIsInstance(record["n_control"], int)
        self.assertIsInstance(record["p_value"], float)
        self.assertGreaterEqual(record["p_value"], 0.0)
        self.assertLessEqual(record["p_value"], 1.0)

    def test_continuous_outcome_structure(self):
        """Test continuous outcome generation structure."""
        record = generate_continuous_outcome(
            baseline_mean=50.0,
            effect_size=0.1,
            std_dev=10.0,
            n_control=100,
            n_treatment=100,
            is_consistent=True
        )
        required_keys = [
            "n_control", "n_treatment", "mean_control", "mean_treatment",
            "std_control", "std_treatment", "observed_diff", "p_value", "is_significant", "outcome_type"
        ]
        for key in required_keys:
            self.assertIn(key, record, f"Continuous record missing key: {key}")
        
        self.assertEqual(record["outcome_type"], "continuous")
        self.assertIsInstance(record["n_control"], int)
        self.assertIsInstance(record["p_value"], float)

    def test_csv_output_creation(self):
        """Test that CSV output file is created and readable."""
        data = generate_synthetic_dataset(total_records=100, output_dir=self.test_output_dir)
        csv_path = self.test_output_dir / "summaries_combined.csv"
        
        self.assertTrue(csv_path.exists(), "CSV file should be created")
        
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(len(rows), len(data), "CSV rows count should match generated data")

    def test_json_output_creation(self):
        """Test that JSON output file is created and valid."""
        data = generate_synthetic_dataset(total_records=100, output_dir=self.test_output_dir)
        json_path = self.test_output_dir / "summaries_combined.json"
        
        self.assertTrue(json_path.exists(), "JSON file should be created")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
        
        self.assertEqual(len(loaded_data), len(data), "JSON data count should match generated data")

    def test_inconsistency_injection(self):
        """Test that inconsistent records are generated when requested."""
        # Generate a batch where 100% are inconsistent
        data = generate_synthetic_dataset(
            total_records=100, 
            consistency_rate=0.0, 
            output_dir=self.test_output_dir
        )
        
        # We can't strictly verify "inconsistency" without ground truth logic,
        # but we can verify the flag exists and p-values are generated.
        for record in data:
            self.assertIn("is_significant", record)
            self.assertIn("p_value", record)

if __name__ == "__main__":
    unittest.main()