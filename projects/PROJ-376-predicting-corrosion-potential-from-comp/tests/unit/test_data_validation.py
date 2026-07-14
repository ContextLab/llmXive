"""
Unit tests for schema validation logic.

This test suite validates the functions in code/utils/validation.py.
These tests are designed to fail before the implementation of T012-T017
(data ingestion and preprocessing) to ensure the validation layer is
correctly integrated into the pipeline.
"""
import unittest
import sys
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, field

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.exceptions import SchemaMismatchError, DataInsufficientError
from utils.validation import validate_non_nulls, validate_schema_structure, filter_null_records
from data.models import AlloyRecord, EnvironmentRecord, CorrosionMeasurement


class TestSchemaValidationLogic(unittest.TestCase):
    """Unit tests for schema validation utilities."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_alloy = AlloyRecord(
            alloy_id="AL-001",
            composition={"Fe": 0.7, "Cr": 0.2, "Ni": 0.1},
            specific_alloy_designation_id="304"
        )
        self.sample_env = EnvironmentRecord(
            env_id="ENV-001",
            ph=7.0,
            temperature=25.0,
            electrolyte="NaCl"
        )
        self.sample_meas = CorrosionMeasurement(
            measurement_id="MEAS-001",
            alloy_id="AL-001",
            env_id="ENV-001",
            potential=-0.45,
            timestamp="2023-01-01T00:00:00"
        )

    def test_validate_non_nulls_pass(self):
        """Test that validation passes when no nulls exist in critical fields."""
        records = [self.sample_alloy, self.sample_env, self.sample_meas]
        # Define critical fields for each record type
        critical_fields = {
            "AlloyRecord": {"alloy_id", "composition"},
            "EnvironmentRecord": {"env_id", "ph", "temperature"},
            "CorrosionMeasurement": {"measurement_id", "alloy_id", "env_id", "potential"}
        }
        
        # This should not raise an exception
        try:
            validate_non_nulls(records, critical_fields)
            passed = True
        except SchemaMismatchError:
            passed = False
        
        self.assertTrue(passed, "Validation should pass for records without nulls in critical fields")

    def test_validate_non_nulls_fail_missing_field(self):
        """Test that validation fails when a critical field is missing (None)."""
        # Create a record with a None critical field
        bad_record = CorrosionMeasurement(
            measurement_id="MEAS-BAD",
            alloy_id=None,  # Critical field is None
            env_id="ENV-001",
            potential=-0.45,
            timestamp="2023-01-01T00:00:00"
        )
        
        records = [self.sample_alloy, self.sample_env, bad_record]
        critical_fields = {
            "CorrosionMeasurement": {"measurement_id", "alloy_id", "env_id", "potential"}
        }

        with self.assertRaises(SchemaMismatchError) as context:
            validate_non_nulls(records, critical_fields)
        
        self.assertIn("alloy_id", str(context.exception))

    def test_validate_schema_structure_pass(self):
        """Test schema structure validation with correct data types."""
        data = {
            "alloy_id": "AL-001",
            "composition": {"Fe": 0.7},
            "specific_alloy_designation_id": "304"
        }
        
        # This should not raise an exception
        try:
            validate_schema_structure(data, AlloyRecord)
            passed = True
        except SchemaMismatchError:
            passed = False

        self.assertTrue(passed, "Validation should pass for correctly structured data")

    def test_validate_schema_structure_fail_missing_field(self):
        """Test schema structure validation fails when required field is missing."""
        data = {
            "alloy_id": "AL-001",
            # Missing 'composition' which is required
            "specific_alloy_designation_id": "304"
        }

        with self.assertRaises(SchemaMismatchError):
            validate_schema_structure(data, AlloyRecord)

    def test_filter_null_records_removes_invalid(self):
        """Test that filter_null_records removes records with null critical fields."""
        valid_record = self.sample_alloy
        invalid_record = AlloyRecord(
            alloy_id=None,
            composition={"Fe": 0.7},
            specific_alloy_designation_id="304"
        )
        
        records = [valid_record, invalid_record]
        critical_fields = {"AlloyRecord": {"alloy_id", "composition"}}

        filtered = filter_null_records(records, critical_fields)

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].alloy_id, valid_record.alloy_id)

    def test_filter_null_records_raises_if_all_filtered(self):
        """Test that filter_null_records raises DataInsufficientError if all records are removed."""
        invalid_record = AlloyRecord(
            alloy_id=None,
            composition=None,
            specific_alloy_designation_id="304"
        )
        
        records = [invalid_record]
        critical_fields = {"AlloyRecord": {"alloy_id", "composition"}}

        with self.assertRaises(DataInsufficientError):
            filter_null_records(records, critical_fields)

    def test_filter_null_records_raises_if_below_threshold(self):
        """Test that filter_null_records raises DataInsufficientError if count < min_count."""
        valid_record = self.sample_alloy
        invalid_record = AlloyRecord(
            alloy_id=None,
            composition={"Fe": 0.7},
            specific_alloy_designation_id="304"
        )
        
        records = [valid_record, invalid_record]
        critical_fields = {"AlloyRecord": {"alloy_id", "composition"}}

        # Set min_count higher than the number of valid records
        with self.assertRaises(DataInsufficientError):
            filter_null_records(records, critical_fields, min_count=5)


if __name__ == '__main__':
    unittest.main()