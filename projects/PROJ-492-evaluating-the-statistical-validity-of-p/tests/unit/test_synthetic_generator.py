"""
Unit tests for the synthetic dataset generator (T026).

Verifies:
1. Script runs without error.
2. Output files are created.
3. Record count >= 10,000.
4. Both binary and continuous outcomes are present.
"""
import csv
import json
import os
import tempfile
from pathlib import Path
from unittest import TestCase

import numpy as np

# Import the module under test
from code.src.audit.synthetic import (
    generate_synthetic_dataset,
    verify_outcome_types,
    set_all_seeds,
    TARGET_RECORD_COUNT
)
from code.src.config import SEED

class TestSyntheticGenerator(TestCase):
    
    def setUp(self):
        """Set up temporary directory for test outputs."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.output_dir = self.temp_dir / "data" / "synthetic"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure deterministic seeds
        set_all_seeds(SEED)
    
    def test_001_generates_minimum_records(self):
        """Test that the generator produces at least 10,000 records."""
        records = generate_synthetic_dataset(
            total_count=TARGET_RECORD_COUNT,
            output_dir=self.output_dir
        )
        
        self.assertGreaterEqual(
            len(records), 
            TARGET_RECORD_COUNT,
            f"Expected at least {TARGET_RECORD_COUNT} records, got {len(records)}"
        )
    
    def test_002_creates_csv_file(self):
        """Test that the CSV output file is created."""
        generate_synthetic_dataset(
            total_count=100,  # Small sample for speed
            output_dir=self.output_dir
        )
        
        csv_path = self.output_dir / "synthetic_summaries.csv"
        self.assertTrue(csv_path.exists(), "CSV file not created")
        self.assertGreater(csv_path.stat().st_size, 0, "CSV file is empty")
    
    def test_003_creates_json_file(self):
        """Test that the JSON output file is created."""
        generate_synthetic_dataset(
            total_count=100,
            output_dir=self.output_dir
        )
        
        json_path = self.output_dir / "synthetic_summaries.json"
        self.assertTrue(json_path.exists(), "JSON file not created")
        self.assertGreater(json_path.stat().st_size, 0, "JSON file is empty")
    
    def test_004_both_outcome_types_present(self):
        """Test that both binary and continuous outcomes are present."""
        records = generate_synthetic_dataset(
            total_count=1000,
            output_dir=self.output_dir
        )
        
        b_count, c_count, is_valid = verify_outcome_types(records)
        
        self.assertTrue(is_valid, "Verification failed: missing outcome types")
        self.assertGreater(b_count, 0, "No binary outcomes found")
        self.assertGreater(c_count, 0, "No continuous outcomes found")
    
    def test_005_record_structure(self):
        """Test that each record has required fields."""
        records = generate_synthetic_dataset(
            total_count=10,
            output_dir=self.output_dir
        )
        
        required_fields = [
            "id", "url", "domain", "year", "outcome_type", 
            "n_control", "n_treatment", "p_value", "effect_size"
        ]
        
        for record in records:
            for field in required_fields:
                self.assertIn(field, record, f"Missing field: {field}")
    
    def test_006_p_value_range(self):
        """Test that p-values are within valid range [0, 1]."""
        records = generate_synthetic_dataset(
            total_count=100,
            output_dir=self.output_dir
        )
        
        for record in records:
            p_val = record["p_value"]
            self.assertGreaterEqual(p_val, 0.0)
            self.assertLessEqual(p_val, 1.0)
    
    def test_007_sample_sizes_positive(self):
        """Test that sample sizes are positive integers."""
        records = generate_synthetic_dataset(
            total_count=100,
            output_dir=self.output_dir
        )
        
        for record in records:
            self.assertGreater(record["n_control"], 0)
            self.assertGreater(record["n_treatment"], 0)
    
    def test_008_file_contents_match_record_count(self):
        """Test that CSV and JSON files contain the same number of records."""
        records = generate_synthetic_dataset(
            total_count=500,
            output_dir=self.output_dir
        )
        
        # Check CSV
        csv_path = self.output_dir / "synthetic_summaries.csv"
        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            csv_count = sum(1 for _ in reader)
        
        # Check JSON
        json_path = self.output_dir / "synthetic_summaries.json"
        with open(json_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)
            json_count = len(json_data)
        
        self.assertEqual(csv_count, json_count, "Record count mismatch between CSV and JSON")
        self.assertEqual(csv_count, len(records), "Record count mismatch with in-memory data")

if __name__ == "__main__":
    import unittest
    unittest.main()