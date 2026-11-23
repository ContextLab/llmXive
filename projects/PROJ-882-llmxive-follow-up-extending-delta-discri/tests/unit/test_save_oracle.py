"""
Unit tests for T015: save_oracle_results.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from data.save_oracle_results import load_schema, validate_against_schema


class TestSaveOracleResults(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.valid_data = [
            {
                "token_id": 1,
                "coefficient": 0.5,
                "variance_check": True,
                "example_id": "100"
            },
            {
                "token_id": 2,
                "coefficient": -0.2,
                "variance_check": True,
                "example_id": "100"
            }
        ]
        
        # Create a temporary schema file
        self.schema_content = {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["token_id", "coefficient", "variance_check"],
                "properties": {
                    "token_id": {"type": "integer"},
                    "coefficient": {"type": "number"},
                    "variance_check": {"type": "boolean"},
                    "example_id": {"type": "string"}
                }
            }
        }
        self.temp_schema_dir = tempfile.mkdtemp()
        self.schema_path = Path(self.temp_schema_dir) / "schema.json"
        with open(self.schema_path, 'w') as f:
            json.dump(self.schema_content, f)

    def tearDown(self):
        """Clean up."""
        import shutil
        shutil.rmtree(self.temp_schema_dir)

    def test_load_schema_valid(self):
        """Test loading a valid schema."""
        schema = load_schema(self.schema_path)
        self.assertEqual(schema['type'], 'array')
        self.assertIn('items', schema)

    def test_load_schema_missing_file(self):
        """Test loading a missing schema raises error."""
        with self.assertRaises(FileNotFoundError):
            load_schema(Path("/non/existent/path.yaml"))

    def test_validate_against_schema_valid(self):
        """Test validation with valid data."""
        schema = load_schema(self.schema_path)
        result = validate_against_schema(self.valid_data, schema)
        self.assertTrue(result)

    def test_validate_against_schema_missing_field(self):
        """Test validation fails on missing required field."""
        invalid_data = [
            {
                "token_id": 1,
                # missing coefficient
                "variance_check": True
            }
        ]
        schema = load_schema(self.schema_path)
        result = validate_against_schema(invalid_data, schema)
        self.assertFalse(result)

    def test_validate_against_schema_wrong_type(self):
        """Test validation fails on wrong type."""
        invalid_data = [
            {
                "token_id": "not_an_int", # should be int
                "coefficient": 0.5,
                "variance_check": True
            }
        ]
        schema = load_schema(self.schema_path)
        # The validator checks types in the properties
        result = validate_against_schema(invalid_data, schema)
        # Our validator might just warn or fail. 
        # Based on implementation: it checks isinstance(token_id, int)
        self.assertFalse(result)

    def test_validate_nan(self):
        """Test validation fails on NaN coefficient."""
        invalid_data = [
            {
                "token_id": 1,
                "coefficient": float('nan'),
                "variance_check": True
            }
        ]
        schema = load_schema(self.schema_path)
        result = validate_against_schema(invalid_data, schema)
        self.assertFalse(result)

    def test_validate_inf(self):
        """Test validation fails on Inf coefficient."""
        invalid_data = [
            {
                "token_id": 1,
                "coefficient": float('inf'),
                "variance_check": True
            }
        ]
        schema = load_schema(self.schema_path)
        result = validate_against_schema(invalid_data, schema)
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()