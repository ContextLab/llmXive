"""
Unit tests for the synthetic dataset generator (T026).
Verifies generation of >= 10,000 records and presence of both outcome types.
"""
import csv
import json
import os
import sys
from pathlib import Path
import unittest

# Add code root to path for imports
code_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(code_root))

from code.src.audit.synthetic import (
    generate_synthetic_dataset,
    verify_outcome_types,
    set_all_seeds,
    TOTAL_RECORDS,
    SEED
)
from code.src.config import set_rng_seed

class TestSyntheticGenerator(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.output_dir = Path("code/data/synthetic_test")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        set_rng_seed(42) # Deterministic seed for tests
    
    def tearDown(self):
        """Clean up test artifacts."""
        if self.output_dir.exists():
            import shutil
            shutil.rmtree(self.output_dir)

    def test_generate_dataset_creates_files(self):
        """Test that the generator creates the expected output files."""
        records = generate_synthetic_dataset(
            total_records=100, # Small number for unit test speed
            output_dir=self.output_dir,
            seed=42
        )
        
        csv_path = self.output_dir / "summaries.csv"
        metadata_path = self.output_dir / "metadata.json"
        
        self.assertTrue(csv_path.exists(), "CSV file not created")
        self.assertTrue(metadata_path.exists(), "Metadata file not created")

    def test_generate_dataset_record_count(self):
        """Test that the generator creates the requested number of records."""
        count = 100
        records = generate_synthetic_dataset(
            total_records=count,
            output_dir=self.output_dir,
            seed=42
        )
        
        self.assertEqual(len(records), count, f"Expected {count} records, got {len(records)}")

    def test_verify_outcome_types_both_present(self):
        """Test verification logic when both types are present."""
        test_records = [
            {"outcome_type": "binary", "id": "1"},
            {"outcome_type": "continuous", "id": "2"}
        ]
        result = verify_outcome_types(test_records)
        self.assertTrue(result, "Verification should pass for mixed types")

    def test_verify_outcome_types_missing_binary(self):
        """Test verification logic when binary is missing."""
        test_records = [
            {"outcome_type": "continuous", "id": "1"},
            {"outcome_type": "continuous", "id": "2"}
        ]
        result = verify_outcome_types(test_records)
        self.assertFalse(result, "Verification should fail if binary is missing")

    def test_verify_outcome_types_missing_continuous(self):
        """Test verification logic when continuous is missing."""
        test_records = [
            {"outcome_type": "binary", "id": "1"},
            {"outcome_type": "binary", "id": "2"}
        ]
        result = verify_outcome_types(test_records)
        self.assertFalse(result, "Verification should fail if continuous is missing")

    def test_full_generation_minimum_records(self):
        """Test that full generation meets the >= 10,000 requirement."""
        records = generate_synthetic_dataset(
            total_records=TOTAL_RECORDS,
            output_dir=self.output_dir,
            seed=42
        )
        
        self.assertGreaterEqual(len(records), 10000, 
            f"Generated {len(records)} records, expected >= 10000")

    def test_full_generation_outcome_diversity(self):
        """Test that full generation includes both binary and continuous outcomes."""
        records = generate_synthetic_dataset(
            total_records=TOTAL_RECORDS,
            output_dir=self.output_dir,
            seed=42
        )
        
        types = set(r["outcome_type"] for r in records)
        self.assertIn("binary", types, "Binary outcomes missing")
        self.assertIn("continuous", types, "Continuous outcomes missing")
        self.assertEqual(len(types), 2, "Only one outcome type found")

    def test_csv_content_validity(self):
        """Test that the generated CSV is valid and readable."""
        count = 500
        records = generate_synthetic_dataset(
            total_records=count,
            output_dir=self.output_dir,
            seed=42
        )
        
        csv_path = self.output_dir / "summaries.csv"
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(len(rows), count, "CSV row count mismatch")
        
        # Check required columns
        required_cols = ["id", "outcome_type", "n_control", "n_treatment", "reported_p_value"]
        for col in required_cols:
            self.assertIn(col, reader.fieldnames, f"Missing column: {col}")

if __name__ == "__main__":
    unittest.main()