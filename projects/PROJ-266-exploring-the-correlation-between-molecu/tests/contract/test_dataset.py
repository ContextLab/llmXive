"""
Contract tests for the Caco-2 dataset against the schema defined in specs/001-molecular-flexibility-permeability/contracts/dataset.schema.yaml.

These tests validate that the data produced by T009 (retrieval) and T010 (preprocessing)
strictly adheres to the defined JSON schema.
"""
import json
import os
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List

# Attempt to import jsonschema; if missing, provide a mock or fail loudly
try:
    import jsonschema
    from jsonschema import validate, ValidationError
except ImportError:
    # Fallback: If jsonschema is not installed, we cannot validate.
    # The task requires real validation, so we raise an error if missing.
    print("ERROR: 'jsonschema' package is required for contract tests. Install via: pip install jsonschema")
    raise RuntimeError("Missing dependency: jsonschema")

from utils.config import get_project_root


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the JSON schema from the specified path."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_csv_as_dicts(csv_path: Path) -> List[Dict[str, Any]]:
    """Load a CSV file into a list of dictionaries."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Data file not found: {csv_path}")
    with open(csv_path, 'r', encoding='utf-8') as f:
        # Simple CSV parser to avoid pandas dependency in tests if not needed,
        # but using csv module is safer for standard library.
        import csv
        reader = csv.DictReader(f)
        return list(reader)


class TestDatasetSchema(unittest.TestCase):
    """
    Validates the dataset against the schema defined in T007.
    """

    @classmethod
    def setUpClass(cls):
        """Set up paths and load schema once."""
        cls.project_root = get_project_root()
        cls.schema_path = cls.project_root / "specs" / "001-molecular-flexibility-permeability" / "contracts" / "dataset.schema.yaml"
        
        # Note: The schema is YAML, but jsonschema expects a dict.
        # We need to parse YAML. If PyYAML is missing, we handle it.
        try:
            import yaml
            with open(cls.schema_path, 'r') as f:
                cls.schema = yaml.safe_load(f)
        except ImportError:
            raise RuntimeError("PyYAML is required to load the schema file.")
        
        # Determine the data file path. 
        # T010 produces 'data/processed/caco2_preprocessed.csv'
        cls.data_path = cls.project_root / "data" / "processed" / "caco2_preprocessed.csv"

    def test_schema_exists(self):
        """Verify the schema file exists and is valid."""
        self.assertTrue(self.schema_path.exists(), "Schema file missing")
        self.assertIsInstance(self.schema, dict, "Schema must be a dictionary")
        self.assertIn("properties", self.schema, "Schema must define 'properties'")

    def test_data_file_exists(self):
        """Verify the preprocessed data file exists."""
        self.assertTrue(self.data_path.exists(), "Preprocessed data file missing. Run T010 first.")

    def test_required_fields_present(self):
        """Check that all required fields defined in schema are present in data."""
        if not self.data_path.exists():
            self.skipTest("Data file missing")
        
        data = load_csv_as_dicts(self.data_path)
        self.assertGreater(len(data), 0, "Data file is empty")

        required_fields = self.schema.get("required", [])
        properties = self.schema.get("properties", {})

        for record in data:
            for field in required_fields:
                self.assertIn(field, record, f"Required field '{field}' missing in record")

    def test_data_types_match_schema(self):
        """Validate that data types in CSV match the schema definitions."""
        if not self.data_path.exists():
            self.skipTest("Data file missing")

        data = load_csv_as_dicts(self.data_path)
        properties = self.schema.get("properties", {})

        for record in data:
            for field, definition in properties.items():
                if field not in record:
                    continue # Handled by required check

                expected_type = definition.get("type")
                value = record[field]

                # Type mapping from JSON Schema to Python
                if expected_type == "string":
                    self.assertIsInstance(value, str, f"Field {field} should be string")
                elif expected_type == "number":
                    # CSV reads as string, so we try to parse
                    try:
                        float(value)
                    except ValueError:
                        self.fail(f"Field {field} with value '{value}' is not a valid number")
                elif expected_type == "integer":
                    try:
                        int(value)
                    except ValueError:
                        self.fail(f"Field {field} with value '{value}' is not a valid integer")

    def test_schema_validation_full(self):
        """Run full jsonschema validation against the data records."""
        if not self.data_path.exists():
            self.skipTest("Data file missing")

        data = load_csv_as_dicts(self.data_path)
        
        # jsonschema.validate expects a single instance. We validate each row.
        for i, record in enumerate(data):
            try:
                # Convert numeric strings to floats/integers for validation if needed
                # The schema expects numbers, CSV gives strings. 
                # We perform a manual conversion for validation purposes or rely on the schema
                # to be lenient. Ideally, the schema should define pattern or we cast.
                # Here, we cast to match the expected type in the schema.
                validated_record = {}
                for key, val in record.items():
                    if key in self.schema.get("properties", {}):
                        p_type = self.schema["properties"][key].get("type")
                        if p_type == "number" or p_type == "integer":
                            validated_record[key] = float(val) if val else None
                        else:
                            validated_record[key] = val
                    else:
                        validated_record[key] = val
                
                validate(instance=validated_record, schema=self.schema)
            except ValidationError as e:
                self.fail(f"Record {i} failed schema validation: {e.message}")

    def test_null_constraints(self):
        """Ensure fields marked as required are not NULL/empty."""
        if not self.data_path.exists():
            self.skipTest("Data file missing")

        data = load_csv_as_dicts(self.data_path)
        required_fields = self.schema.get("required", [])

        for i, record in enumerate(data):
            for field in required_fields:
                value = record.get(field)
                if value is None or value == "":
                    self.fail(f"Record {i} has NULL/empty value for required field '{field}'")


if __name__ == '__main__':
    unittest.main()