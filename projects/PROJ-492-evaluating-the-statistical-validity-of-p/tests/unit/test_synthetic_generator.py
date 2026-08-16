"""Unit tests for synthetic dataset generator (T026)."""
import csv
import json
import os
import tempfile
from pathlib import Path
from unittest import TestCase

import numpy as np

from code.src.audit.synthetic import (
    generate_binary_test_record,
    generate_continuous_test_record,
    generate_synthetic_dataset,
    main,
    set_seeds
)
from code.src.config import SEED


class TestSyntheticGenerator(TestCase):
    """Tests for the synthetic dataset generator."""

    def setUp(self):
        """Set up test fixtures."""
        self.seed = SEED
        self.test_domain = "example.com"
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)

    def test_set_seeds_deterministic(self):
        """Test that set_seeds produces deterministic results."""
        set_seeds(self.seed)
        result1 = generate_binary_test_record(True, self.test_domain, 1)
        
        set_seeds(self.seed)
        result2 = generate_binary_test_record(True, self.test_domain, 1)
        
        self.assertEqual(result1["id"], result2["id"])
        self.assertEqual(result1["baseline_conversion_rate"], result2["baseline_conversion_rate"])
        self.assertEqual(result1["reported_p_value"], result2["reported_p_value"])

    def test_binary_record_structure(self):
        """Test that binary records have all required fields."""
        record = generate_binary_test_record(True, self.test_domain, 1)
        
        required_fields = [
            "id", "url", "domain", "test_date", "outcome_type",
            "n_control", "n_treatment", "baseline_conversion_rate",
            "treatment_conversion_rate", "reported_p_value", "reported_effect_size",
            "reported_confidence_interval", "test_duration_days",
            "is_consistent", "inconsistency_type"
        ]
        
        for field in required_fields:
            self.assertIn(field, record, f"Missing required field: {field}")

    def test_continuous_record_structure(self):
        """Test that continuous records have all required fields."""
        record = generate_continuous_test_record(True, self.test_domain, 1)
        
        required_fields = [
            "id", "url", "domain", "test_date", "outcome_type",
            "n_control", "n_treatment", "baseline_mean", "baseline_std",
            "treatment_mean", "treatment_std", "reported_p_value",
            "reported_effect_size", "reported_confidence_interval",
            "test_duration_days", "is_consistent", "inconsistency_type"
        ]
        
        for field in required_fields:
            self.assertIn(field, record, f"Missing required field: {field}")

    def test_binary_record_value_ranges(self):
        """Test that binary record values are within expected ranges."""
        record = generate_binary_test_record(True, self.test_domain, 1)
        
        self.assertGreaterEqual(record["n_control"], 1000)
        self.assertLessEqual(record["n_control"], 50000)
        self.assertGreaterEqual(record["n_treatment"], 1000)
        self.assertLessEqual(record["n_treatment"], 50000)
        self.assertGreaterEqual(record["baseline_conversion_rate"], 0.05)
        self.assertLessEqual(record["baseline_conversion_rate"], 0.30)
        self.assertGreaterEqual(record["reported_p_value"], 0.001)
        self.assertLessEqual(record["reported_p_value"], 0.999)
        self.assertEqual(record["outcome_type"], "binary")

    def test_continuous_record_value_ranges(self):
        """Test that continuous record values are within expected ranges."""
        record = generate_continuous_test_record(True, self.test_domain, 1)
        
        self.assertGreaterEqual(record["n_control"], 500)
        self.assertLessEqual(record["n_control"], 20000)
        self.assertGreaterEqual(record["n_treatment"], 500)
        self.assertLessEqual(record["n_treatment"], 20000)
        self.assertGreaterEqual(record["baseline_mean"], 10.0)
        self.assertLessEqual(record["baseline_mean"], 100.0)
        self.assertGreaterEqual(record["reported_p_value"], 0.001)
        self.assertLessEqual(record["reported_p_value"], 0.999)
        self.assertEqual(record["outcome_type"], "continuous")

    def test_consistency_flag(self):
        """Test that consistency flag is set correctly."""
        consistent_record = generate_binary_test_record(True, self.test_domain, 1)
        inconsistent_record = generate_binary_test_record(False, self.test_domain, 2)
        
        self.assertTrue(consistent_record["is_consistent"])
        self.assertFalse(inconsistent_record["is_consistent"])
        
        if consistent_record["is_consistent"]:
            self.assertIsNone(consistent_record["inconsistency_type"])
        
        if not inconsistent_record["is_consistent"]:
            self.assertIsNotNone(inconsistent_record["inconsistency_type"])
            self.assertIn(inconsistent_record["inconsistency_type"], 
                         ["p_value_drift", "effect_size_drift", "sample_size_mismatch"])

    def test_generate_synthetic_dataset_count(self):
        """Test that the dataset generator produces at least 10,000 records."""
        binary_records, continuous_records = generate_synthetic_dataset(self.seed)
        
        total_records = len(binary_records) + len(continuous_records)
        self.assertGreaterEqual(total_records, 10000, 
                               f"Expected at least 10,000 records, got {total_records}")
        
        # Check that we have both binary and continuous records
        self.assertGreater(len(binary_records), 0, "No binary records generated")
        self.assertGreater(len(continuous_records), 0, "No continuous records generated")

    def test_generate_synthetic_dataset_types(self):
        """Test that the dataset contains both binary and continuous outcomes."""
        binary_records, continuous_records = generate_synthetic_dataset(self.seed)
        
        for record in binary_records:
            self.assertEqual(record["outcome_type"], "binary")
        
        for record in continuous_records:
            self.assertEqual(record["outcome_type"], "continuous")

    def test_main_creates_files(self):
        """Test that main() creates the expected output files."""
        original_cwd = os.getcwd()
        temp_output_dir = Path(self.temp_dir) / "data" / "synthetic"
        temp_output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            os.chdir(self.temp_dir)
            main()
            
            binary_path = temp_output_dir / "ab_summaries_binary.csv"
            continuous_path = temp_output_dir / "ab_summaries_continuous.csv"
            combined_path = temp_output_dir / "ab_summaries_combined.json"
            
            self.assertTrue(binary_path.exists(), "Binary CSV not created")
            self.assertTrue(continuous_path.exists(), "Continuous CSV not created")
            self.assertTrue(combined_path.exists(), "Combined JSON not created")
            
            # Verify CSV has content
            with open(binary_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                self.assertGreaterEqual(len(rows), 1000, "Binary CSV has too few rows")
            
            with open(continuous_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                self.assertGreaterEqual(len(rows), 1000, "Continuous CSV has too few rows")
            
            # Verify JSON has content
            with open(combined_path, 'r') as f:
                data = json.load(f)
                self.assertIn("binary_outcomes", data)
                self.assertIn("continuous_outcomes", data)
                self.assertGreaterEqual(len(data["binary_outcomes"]), 1000)
                self.assertGreaterEqual(len(data["continuous_outcomes"]), 1000)
                
        finally:
            os.chdir(original_cwd)

    def test_domain_diversity(self):
        """Test that records are distributed across multiple domains."""
        binary_records, continuous_records = generate_synthetic_dataset(self.seed)
        all_records = binary_records + continuous_records
        
        domains = set(record["domain"] for record in all_records)
        self.assertGreater(len(domains), 1, "All records have the same domain")
        
        # Check that we have at least 5 different domains
        self.assertGreaterEqual(len(domains), 5, 
                               f"Expected at least 5 domains, got {len(domains)}")

    def test_record_id_uniqueness(self):
        """Test that all record IDs are unique."""
        binary_records, continuous_records = generate_synthetic_dataset(self.seed)
        all_records = binary_records + continuous_records
        
        ids = [record["id"] for record in all_records]
        unique_ids = set(ids)
        
        self.assertEqual(len(ids), len(unique_ids), 
                       "Duplicate record IDs found in generated dataset")