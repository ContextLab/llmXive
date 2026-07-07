"""
Unit tests for the synthetic dataset generator (T026).

Verifies:
- Generation of at least 10,000 records
- Presence of both binary and continuous outcomes
- Data integrity of generated records
"""
import csv
import json
import os
import sys
from pathlib import Path
import unittest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.src.audit.synthetic import (
    generate_synthetic_dataset,
    verify_outcome_types,
    write_csv_output,
    write_metadata,
    set_all_seeds,
    MIN_RECORDS
)

class TestSyntheticGenerator(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        set_all_seeds(42)  # Deterministic for tests
        cls.test_dir = Path("data/test_synthetic")
        cls.test_dir.mkdir(parents=True, exist_ok=True)
    
    def test_minimum_record_count(self):
        """Verify that generation produces at least 10,000 records."""
        binary, continuous = generate_synthetic_dataset(target_count=MIN_RECORDS)
        total = len(binary) + len(continuous)
        
        self.assertGreaterEqual(total, MIN_RECORDS, 
            f"Total records {total} is less than minimum {MIN_RECORDS}")
    
    def test_both_outcome_types_present(self):
        """Verify both binary and continuous outcomes are generated."""
        binary, continuous = generate_synthetic_dataset(target_count=MIN_RECORDS)
        
        self.assertGreater(len(binary), 0, "No binary records generated")
        self.assertGreater(len(continuous), 0, "No continuous records generated")
        
        # Verify types in data
        for rec in binary:
            self.assertEqual(rec["outcome_type"], "binary")
        
        for rec in continuous:
            self.assertEqual(rec["outcome_type"], "continuous")
    
    def test_verify_outcome_types_function(self):
        """Test the verification function logic."""
        # Valid case
        binary = [{"outcome_type": "binary"} for _ in range(1001)]
        continuous = [{"outcome_type": "continuous"} for _ in range(1001)]
        result = verify_outcome_types(binary, continuous)
        self.assertTrue(result)
        
        # Invalid case: too few binary
        binary = [{"outcome_type": "binary"} for _ in range(999)]
        continuous = [{"outcome_type": "continuous"} for _ in range(1001)]
        result = verify_outcome_types(binary, continuous)
        self.assertFalse(result)
    
    def test_csv_output_structure(self):
        """Verify CSV output has correct headers and data."""
        binary, continuous = generate_synthetic_dataset(target_count=100)
        
        binary_path = self.test_dir / "test_binary.csv"
        continuous_path = self.test_dir / "test_continuous.csv"
        
        write_csv_output(binary, binary_path)
        write_csv_output(continuous, continuous_path)
        
        # Check binary CSV
        with open(binary_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 100)
            self.assertIn("baseline_rate", reader.fieldnames)
            self.assertIn("treatment_rate", reader.fieldnames)
            self.assertIn("p_value", reader.fieldnames)
        
        # Check continuous CSV
        with open(continuous_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            self.assertEqual(len(rows), 100)
            self.assertIn("baseline_mean", reader.fieldnames)
            self.assertIn("treatment_mean", reader.fieldnames)
            self.assertIn("baseline_std", reader.fieldnames)
    
    def test_metadata_generation(self):
        """Verify metadata JSON contains required fields."""
        binary, continuous = generate_synthetic_dataset(target_count=100)
        metadata_path = self.test_dir / "test_metadata.json"
        
        write_metadata(len(binary), len(continuous), metadata_path)
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        self.assertIn("total_records", metadata)
        self.assertIn("binary_count", metadata)
        self.assertIn("continuous_count", metadata)
        self.assertIn("seed", metadata)
        self.assertEqual(metadata["total_records"], 200)
    
    def test_data_integrity_binary(self):
        """Verify binary records have valid probability values."""
        binary, _ = generate_synthetic_dataset(target_count=50)
        
        for rec in binary:
            self.assertGreaterEqual(rec["baseline_rate"], 0.01)
            self.assertLessEqual(rec["baseline_rate"], 0.99)
            self.assertGreaterEqual(rec["treatment_rate"], 0.01)
            self.assertLessEqual(rec["treatment_rate"], 0.99)
            self.assertGreaterEqual(rec["p_value"], 0.001)
            self.assertLessEqual(rec["p_value"], 0.999)
            self.assertIsInstance(rec["n_control"], int)
            self.assertIsInstance(rec["n_treatment"], int)
    
    def test_data_integrity_continuous(self):
        """Verify continuous records have valid statistical values."""
        _, continuous = generate_synthetic_dataset(target_count=50)
        
        for rec in continuous:
            self.assertGreater(rec["baseline_mean"], 0)
            self.assertGreater(rec["treatment_mean"], 0)
            self.assertGreater(rec["baseline_std"], 0)
            self.assertGreater(rec["treatment_std"], 0)
            self.assertGreaterEqual(rec["p_value"], 0.001)
            self.assertLessEqual(rec["p_value"], 0.999)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test files."""
        import shutil
        if cls.test_dir.exists():
            shutil.rmtree(cls.test_dir)

if __name__ == '__main__':
    unittest.main()
