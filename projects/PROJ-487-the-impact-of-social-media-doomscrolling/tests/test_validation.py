"""
Unit tests for schema validation utilities.
"""
import os
import sys
import unittest
import tempfile
import yaml
import pandas as pd
import json
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.validation import (
    ValidationError, 
    load_schema, 
    validate_field_type, 
    validate_value_constraints, 
    validate_record, 
    validate_dataset_file, 
    validate_output_file,
    validate_against_schema
)

class TestSchemaLoading(unittest.TestCase):
    def test_load_valid_schema(self):
        schema_content = {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            }
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(schema_content, f)
            temp_path = f.name

        try:
            loaded = load_schema(temp_path)
            self.assertEqual(loaded['type'], 'object')
            self.assertIn('name', loaded['properties'])
        finally:
            os.unlink(temp_path)

    def test_load_missing_schema(self):
        with self.assertRaises(ValidationError):
            load_schema('/nonexistent/path/schema.yaml')

    def test_load_invalid_yaml_schema(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name

        try:
            with self.assertRaises(ValidationError):
                load_schema(temp_path)
        finally:
            os.unlink(temp_path)

class TestFieldTypeValidation(unittest.TestCase):
    def test_string_type(self):
        self.assertTrue(validate_field_type("hello", "string"))
        self.assertFalse(validate_field_type(123, "string"))

    def test_integer_type(self):
        self.assertTrue(validate_field_type(123, "integer"))
        self.assertFalse(validate_field_type(12.5, "integer"))
        self.assertFalse(validate_field_type(True, "integer")) # bool is subclass of int, but not int in JSON

    def test_number_type(self):
        self.assertTrue(validate_field_type(123, "number"))
        self.assertTrue(validate_field_type(12.5, "number"))
        self.assertFalse(validate_field_type("123", "number"))

    def test_boolean_type(self):
        self.assertTrue(validate_field_type(True, "boolean"))
        self.assertTrue(validate_field_type(False, "boolean"))
        self.assertFalse(validate_field_type(1, "boolean"))

class TestValueConstraints(unittest.TestCase):
    def test_minimum_constraint(self):
        self.assertTrue(validate_value_constraints(5, {"minimum": 0}))
        self.assertFalse(validate_value_constraints(-1, {"minimum": 0}))

    def test_maximum_constraint(self):
        self.assertTrue(validate_value_constraints(5, {"maximum": 10}))
        self.assertFalse(validate_value_constraints(15, {"maximum": 10}))

    def test_pattern_constraint(self):
        self.assertTrue(validate_value_constraints("ABC", {"pattern": r"^[A-Z]+$"}))
        self.assertFalse(validate_value_constraints("Abc", {"pattern": r"^[A-Z]+$"}))

    def test_no_constraints(self):
        self.assertTrue(validate_value_constraints("anything", {}))

class TestRecordValidation(unittest.TestCase):
    def test_valid_record(self):
        schema = {
            "type": "object",
            "required": ["id", "value"],
            "properties": {
                "id": {"type": "integer"},
                "value": {"type": "number"}
            }
        }
        record = {"id": 1, "value": 3.14}
        errors = validate_record(record, schema)
        self.assertEqual(len(errors), 0)

    def test_invalid_type_record(self):
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "integer"}
            }
        }
        record = {"id": "not_an_int"}
        errors = validate_record(record, schema)
        self.assertGreater(len(errors), 0)

    def test_missing_required_record(self):
        schema = {
            "type": "object",
            "required": ["id"],
            "properties": {
                "id": {"type": "integer"}
            }
        }
        record = {}
        errors = validate_record(record, schema)
        self.assertGreater(len(errors), 0)

class TestDatasetFileValidation(unittest.TestCase):
    def setUp(self):
        self.schema = {
            "type": "object",
            "required": ["date", "value"],
            "properties": {
                "date": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$"},
                "value": {"type": "number"}
            }
        }
        self.temp_schema = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(self.schema, self.temp_schema)
        self.temp_schema.close()

    def tearDown(self):
        os.unlink(self.temp_schema.name)

    def test_valid_csv(self):
        df = pd.DataFrame({
            "date": ["2023-01-01", "2023-01-02"],
            "value": [10.5, 20.3]
        })
        temp_csv = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        df.to_csv(temp_csv, index=False)
        temp_csv.close()

        try:
            result = validate_dataset_file(temp_csv.name, self.temp_schema.name)
            self.assertTrue(result)
        finally:
            os.unlink(temp_csv.name)

    def test_invalid_csv(self):
        df = pd.DataFrame({
            "date": ["not-a-date", "2023-01-02"],
            "value": [10.5, 20.3]
        })
        temp_csv = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        df.to_csv(temp_csv, index=False)
        temp_csv.close()

        try:
            result = validate_dataset_file(temp_csv.name, self.temp_schema.name)
            self.assertFalse(result)
        finally:
            os.unlink(temp_csv.name)

class TestOutputFileValidation(unittest.TestCase):
    def setUp(self):
        self.schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["success", "failure"]}
            }
        }
        self.temp_schema = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(self.schema, self.temp_schema)
        self.temp_schema.close()

    def tearDown(self):
        os.unlink(self.temp_schema.name)

    def test_valid_json(self):
        data = {"status": "success"}
        temp_json = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(data, temp_json)
        temp_json.close()

        try:
            result = validate_output_file(temp_json.name, self.temp_schema.name)
            self.assertTrue(result)
        finally:
            os.unlink(temp_json.name)

    def test_invalid_json(self):
        data = {"status": "unknown"}
        temp_json = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(data, temp_json)
        temp_json.close()

        try:
            result = validate_output_file(temp_json.name, self.temp_schema.name)
            self.assertFalse(result)
        finally:
            os.unlink(temp_json.name)

if __name__ == '__main__':
    unittest.main()