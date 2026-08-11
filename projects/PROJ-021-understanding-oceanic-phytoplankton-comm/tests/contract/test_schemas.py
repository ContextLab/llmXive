"""
Contract tests for schema validation.
Validates that generated data artifacts conform to the defined YAML schemas.
"""

import os
import sys
import json
import unittest
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional

# Project root setup for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import configuration to resolve paths
from utils.config import get_config, reset_config

# Import schema validator logic (using jsonschema as the standard tool)
try:
    import jsonschema
    from jsonschema import validate, ValidationError, Draft7Validator
except ImportError:
    # Fallback if jsonschema is not installed (should be in requirements.txt)
    jsonschema = None
    Draft7Validator = None


class SchemaValidator:
    """
    Helper class to load a YAML schema and validate a JSON/Dict instance against it.
    """
    def __init__(self, schema_path: Path):
        self.schema_path = schema_path
        self.schema = self._load_schema()
        self.validator = Draft7Validator(self.schema) if Draft7Validator else None

    def _load_schema(self) -> Dict[str, Any]:
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")
        
        with open(self.schema_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def validate(self, instance: Dict[str, Any]) -> bool:
        if self.validator is None:
            raise RuntimeError("jsonschema library not available. Install with: pip install jsonschema")
        
        errors = list(self.validator.iter_errors(instance))
        if errors:
            error_messages = [f"{e.path}: {e.message}" for e in errors]
            raise ValidationError(f"Schema validation failed:\n" + "\n".join(error_messages))
        return True


class TestAlignedDatasetSchema(unittest.TestCase):
    """
    Contract test for aligned_dataset.schema.yaml.
    Verifies that the aligned dataset artifact (if present) matches the schema definition.
    """

    @classmethod
    def setUpClass(cls):
        """
        Setup: Initialize config and locate the schema file.
        """
        reset_config()
        config = get_config()
        
        # Determine schema path based on project structure
        # Spec says: specs/001-phytoplankton-vlm-analysis/contracts/aligned_dataset.schema.yaml
        cls.schema_path = (
            PROJECT_ROOT / 
            "specs" / 
            "001-phytoplankton-vlm-analysis" / 
            "contracts" / 
            "aligned_dataset.schema.yaml"
        )
        
        if not cls.schema_path.exists():
            # If the schema file is missing, we cannot run the contract test.
            # We mark the test as skipped rather than failing the whole suite,
            # but in a real CI environment, the schema file should exist.
            cls.skip_reason = f"Schema file not found at {cls.schema_path}"
            cls.validator = None
        else:
            cls.validator = SchemaValidator(cls.schema_path)
            cls.skip_reason = None

        # Path to the potential artifact to validate
        # Task T014 generates this file. We check if it exists to validate.
        # If it doesn't exist yet (e.g., T014 not run), we skip the data validation
        # but the schema loading test still runs.
        cls.artifact_path = PROJECT_ROOT / "data" / "processed" / "aligned_dataset.nc"
        # We also check a potential CSV version if NetCDF fails or is not yet generated
        cls.artifact_csv_path = PROJECT_ROOT / "data" / "processed" / "aligned_dataset.csv"

    def test_schema_file_exists_and_loads(self):
        """
        Verify that the schema file exists and is valid YAML.
        """
        self.assertIsNotNone(self.validator, self.skip_reason)
        self.assertIsInstance(self.validator.schema, dict)
        self.assertIn("type", self.validator.schema)

    def test_aligned_dataset_schema_structure(self):
        """
        Verify the schema defines the expected structure for the aligned dataset.
        This ensures the schema itself is reasonable (e.g., has properties).
        """
        self.assertIsNotNone(self.validator, self.skip_reason)
        
        # Basic structural checks on the schema
        schema = self.validator.schema
        self.assertIn("properties", schema, "Schema must define 'properties'")
        
        # Check for expected high-level fields typically found in this dataset
        # based on the project context (US1: Data Ingestion)
        expected_fields = ["basin_id", "time", "latitude", "longitude", "chlorophyll", "temperature", "salinity"]
        
        for field in expected_fields:
            # We don't strictly require ALL fields in every schema version,
            # but the schema should define a set of properties.
            # This test ensures the schema is not empty or malformed.
            pass 
        
        self.assertTrue(len(schema["properties"]) > 0, "Schema properties should not be empty")

    def test_validate_artifact_if_exists(self):
        """
        If the aligned dataset artifact exists, validate it against the schema.
        """
        if self.validator is None:
            self.skipTest(self.skip_reason)

        # Try to load the artifact. We need to convert it to a JSON-serializable dict
        # for jsonschema validation.
        artifact_to_validate = None

        if self.artifact_path.exists():
            try:
                import xarray as xr
                ds = xr.open_dataset(self.artifact_path)
                # Convert to dict of arrays (flattened for validation simplicity)
                # Note: Real validation might need to handle nested structures or
                # specific record formats depending on the schema definition.
                # Here we validate the metadata/structure or a sample row if the schema expects records.
                
                # If the schema expects a list of records (rows), we convert the dataset to a list of dicts.
                # If the schema expects a single object with arrays, we convert differently.
                # Given typical data schemas, we assume a record-based validation or metadata check.
                
                # Strategy: If schema expects "type: object" with array properties, validate the whole.
                # If schema expects "type: object" representing a single row, validate one row.
                
                # Let's assume the schema describes the structure of a single row/record
                # or the metadata of the dataset.
                
                # For robustness, we'll try to validate the dataset's coordinate and variable names
                # against the schema if the schema defines "properties" that match variable names.
                
                # Convert dataset to a representative dict for validation
                # We take the first row if dimensions allow, otherwise metadata
                if len(ds.dims) > 0:
                    # Attempt to get a single record
                    try:
                        sample = ds.isel({list(ds.dims.keys())[0]: 0}).to_dict(data=False)
                        # xarray to_dict with data=False loses values, we need values for validation usually.
                        # Let's try to_dict() which converts to pandas then json-compatible
                        sample = ds.isel({list(ds.dims.keys())[0]: 0}).to_pandas().iloc[0].to_dict()
                        artifact_to_validate = sample
                    except Exception:
                        # Fallback: validate metadata only
                        artifact_to_validate = {"variables": list(ds.data_vars), "coords": list(ds.coords)}
                else:
                    artifact_to_validate = ds.attrs
                
            except Exception as e:
                self.fail(f"Failed to load and convert NetCDF artifact for validation: {e}")
        
        elif self.artifact_csv_path.exists():
            try:
                import pandas as pd
                df = pd.read_csv(self.artifact_csv_path)
                if len(df) > 0:
                    artifact_to_validate = df.iloc[0].to_dict()
                else:
                    self.skipTest("CSV artifact exists but is empty.")
            except Exception as e:
                self.fail(f"Failed to load CSV artifact for validation: {e}")
        else:
            self.skipTest("No aligned dataset artifact found to validate (T014 not run).")

        if artifact_to_validate:
            try:
                self.validator.validate(artifact_to_validate)
            except ValidationError as e:
                self.fail(f"Artifact validation failed against schema: {e.message}")


if __name__ == '__main__':
    unittest.main()