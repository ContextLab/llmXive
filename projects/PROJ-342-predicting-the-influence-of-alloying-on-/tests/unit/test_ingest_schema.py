"""
Unit tests for dataset schema validation (User Story 1).

This module validates that the dataset loaded from the Zenodo DOI
conforms to the `dataset.schema.yaml` contract defined in the project specs.
"""
import json
import os
import sys
import unittest
from pathlib import Path
from typing import Any, Dict

# Add project root to path to resolve local imports
# Assumes this file is at tests/unit/test_ingest_schema.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from contracts.schema_loader import (
    DatasetSchemaLoader,
    SchemaValidationError,
    load_dataset_schema,
)
from config.config import get_config


class TestIngestSchema(unittest.TestCase):
    """
    Contract tests for dataset schema validation.
    
    These tests ensure that the data ingestion process produces data
    that strictly adheres to the defined schema requirements (FR-001, SC-003).
    """

    @classmethod
    def setUpClass(cls):
        """
        Load the dataset schema once for all tests in this class.
        """
        # Determine the path to the schema file relative to the project
        schema_path = PROJECT_ROOT / "specs" / "001-predict-tg-metallic-glasses" / "dataset.schema.yaml"
        
        if not schema_path.exists():
            raise FileNotFoundError(
                f"Dataset schema file not found at {schema_path}. "
                "Ensure the schema file exists before running these tests."
            )
        
        cls.schema = load_dataset_schema(str(schema_path))
        cls.loader = DatasetSchemaLoader(cls.schema)

    def test_schema_loads_successfully(self):
        """
        Verify that the schema file itself is valid YAML and loads without error.
        """
        self.assertIsNotNone(self.schema)
        self.assertIn("properties", self.schema)
        self.assertIn("required", self.schema)

    def test_required_fields_exist(self):
        """
        Verify that the schema defines the required fields for metallic glass data.
        Based on the project spec, Tg and composition are critical.
        """
        required_fields = self.schema.get("required", [])
        self.assertIn("Tg", required_fields, "Tg must be a required field in the schema")
        self.assertIn("composition", required_fields, "composition must be a required field in the schema")

    def test_validate_valid_sample_data(self):
        """
        Test validation against a manually constructed valid sample record.
        This ensures the validator logic works correctly for valid input.
        """
        valid_record = {
            "Tg": 350.0,
            "composition": "Zr41.2Ti13.8Cu12.5Ni10Be22.5",
            "doi": "10.5281/zenodo.10043838",
            "source": "zenodo"
        }
        
        # Should not raise an exception
        result = self.loader.validate_record(valid_record)
        self.assertTrue(result.get("valid", False))

    def test_validate_missing_required_field(self):
        """
        Test validation fails when a required field (Tg) is missing.
        """
        invalid_record = {
            "composition": "Zr41.2Ti13.8Cu12.5Ni10Be22.5",
            "doi": "10.5281/zenodo.10043838",
            "source": "zenodo"
            # Missing "Tg"
        }
        
        with self.assertRaises(SchemaValidationError) as context:
            self.loader.validate_record(invalid_record)
        
        self.assertIn("Tg", str(context.exception))

    def test_validate_null_required_field(self):
        """
        Test validation fails when a required field (Tg) is explicitly None.
        """
        invalid_record = {
            "Tg": None,
            "composition": "Zr41.2Ti13.8Cu12.5Ni10Be22.5",
            "doi": "10.5281/zenodo.10043838",
            "source": "zenodo"
        }
        
        with self.assertRaises(SchemaValidationError) as context:
            self.loader.validate_record(invalid_record)
        
        self.assertIn("Tg", str(context.exception))

    def test_validate_empty_composition(self):
        """
        Test validation fails when composition is an empty string.
        """
        invalid_record = {
            "Tg": 350.0,
            "composition": "",
            "doi": "10.5281/zenodo.10043838",
            "source": "zenodo"
        }
        
        with self.assertRaises(SchemaValidationError) as context:
            self.loader.validate_record(invalid_record)
        
        self.assertIn("composition", str(context.exception))

    def test_schema_types_enforced(self):
        """
        Test that type mismatches (e.g., string for Tg) are caught if the schema enforces types.
        """
        # If the schema defines Tg as number, this should fail
        invalid_record = {
            "Tg": "not_a_number",
            "composition": "Zr41.2Ti13.8Cu12.5Ni10Be22.5",
            "doi": "10.5281/zenodo.10043838",
            "source": "zenodo"
        }
        
        # Depending on strictness of the validator, this might raise or return invalid.
        # We expect the validator to catch type errors if defined in schema.
        try:
            result = self.loader.validate_record(invalid_record)
            if not result.get("valid", True):
                self.assertTrue(True) # Expected failure
            else:
                # If it passed, the schema might not be enforcing types strictly in this loader version
                # But for the purpose of this contract test, we assert the schema *should* enforce it.
                # If the loader doesn't enforce types, this test documents that gap.
                self.fail("Schema validation should reject non-numeric Tg if type is defined as number.")
        except SchemaValidationError:
            self.assertTrue(True) # Expected failure

if __name__ == "__main__":
    unittest.main()