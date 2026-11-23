"""
Unit tests for the schema verification logic in code/verify_schemas.py.
"""
import json
import csv
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, mock_open

# Import the module to test
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from verify_schemas import (
    validate_json_list, 
    validate_json_object, 
    validate_csv,
    load_yaml_schema
)

class TestSchemaValidation(unittest.TestCase):

    def setUp(self):
        self.valid_schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "value": {"type": "number"}
            },
            "required": ["id"]
        }

    def test_validate_json_object_valid(self):
        data = {"id": "123", "value": 42.5}
        self.assertTrue(validate_json_object(data, self.valid_schema, Path("test.json")))

    def test_validate_json_object_missing_required(self):
        data = {"value": 42.5}
        self.assertFalse(validate_json_object(data, self.valid_schema, Path("test.json")))

    def test_validate_json_list_valid(self):
        data = [
            {"id": "1", "value": 10},
            {"id": "2", "value": 20}
        ]
        self.assertTrue(validate_json_list(data, self.valid_schema, Path("test.json")))

    def test_validate_json_list_invalid(self):
        data = [
            {"id": "1", "value": 10},
            {"value": 20}  # Missing required 'id'
        ]
        self.assertFalse(validate_json_list(data, self.valid_schema, Path("test.json")))

    def test_validate_csv_valid(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "number"}
            },
            "required": ["name"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            writer = csv.writer(f)
            writer.writerow(["name", "age"])
            writer.writerow(["Alice", "30"])
            writer.writerow(["Bob", "25"])
            temp_path = f.name
        
        try:
            # Mock load_yaml_schema to return our schema directly to avoid file I/O issues in test
            with patch('verify_schemas.load_yaml_schema', return_value=schema):
                result = validate_csv(Path(temp_path), Path("dummy.yaml"))
                self.assertTrue(result)
        finally:
            os.unlink(temp_path)

    def test_validate_csv_missing_header(self):
        schema = {
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "required": ["id"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            writer = csv.writer(f)
            writer.writerow(["wrong_id"])
            writer.writerow(["123"])
            temp_path = f.name
        
        try:
            with patch('verify_schemas.load_yaml_schema', return_value=schema):
                result = validate_csv(Path(temp_path), Path("dummy.yaml"))
                self.assertFalse(result)
        finally:
            os.unlink(temp_path)

    def test_validate_csv_type_mismatch(self):
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "count": {"type": "number"}
            },
            "required": ["id", "count"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            writer = csv.writer(f)
            writer.writerow(["id", "count"])
            writer.writerow(["123", "not_a_number"])
            temp_path = f.name
        
        try:
            with patch('verify_schemas.load_yaml_schema', return_value=schema):
                result = validate_csv(Path(temp_path), Path("dummy.yaml"))
                self.assertFalse(result)
        finally:
            os.unlink(temp_path)

if __name__ == '__main__':
    unittest.main()