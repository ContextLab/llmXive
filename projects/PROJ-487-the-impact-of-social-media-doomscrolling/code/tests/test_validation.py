"""
Unit tests for schema validation utilities.
"""

import os
import sys
import unittest
import tempfile
import yaml
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.validation import (
    validate_field_type,
    validate_value_constraints,
    validate_record,
    validate_dataset_file,
    load_schema,
    validate_against_schema
)


class TestFieldTypeValidation(unittest.TestCase):
    """Tests for validate_field_type function."""

    def test_string_type(self):
        self.assertTrue(validate_field_type("hello", "string"))
        self.assertTrue(validate_field_type("hello", "str"))
        self.assertFalse(validate_field_type(123, "string"))

    def test_integer_type(self):
        self.assertTrue(validate_field_type(42, "integer"))
        self.assertTrue(validate_field_type(42, "int"))
        self.assertFalse(validate_field_type("42", "integer"))
        self.assertTrue(validate_field_type(42.0, "integer"))  # Float that is whole number

    def test_float_type(self):
        self.assertTrue(validate_field_type(3.14, "float"))
        self.assertTrue(validate_field_type(3.14, "number"))
        self.assertTrue(validate_field_type(42, "float"))  # Integer is valid as float
        self.assertFalse(validate_field_type("3.14", "float"))

    def test_boolean_type(self):
        self.assertTrue(validate_field_type(True, "boolean"))
        self.assertTrue(validate_field_type(False, "bool"))
        self.assertFalse(validate_field_type(1, "boolean"))  # 1 is not a boolean

    def test_list_type(self):
        self.assertTrue(validate_field_type([1, 2, 3], "list"))
        self.assertTrue(validate_field_type([1, 2, 3], "array"))
        self.assertFalse(validate_field_type("not a list", "list"))

    def test_dict_type(self):
        self.assertTrue(validate_field_type({"key": "value"}, "dict"))
        self.assertTrue(validate_field_type({"key": "value"}, "object"))
        self.assertFalse(validate_field_type([], "dict"))

    def test_any_type(self):
        self.assertTrue(validate_field_type("anything", "any"))
        self.assertTrue(validate_field_type(123, "any"))
        self.assertTrue(validate_field_type([1, 2], "any"))


class TestValueConstraints(unittest.TestCase):
    """Tests for validate_value_constraints function."""

    def test_min_constraint(self):
        is_valid, _ = validate_value_constraints(5, {'min': 0})
        self.assertTrue(is_valid)
        is_valid, _ = validate_value_constraints(-1, {'min': 0})
        self.assertFalse(is_valid)

    def test_max_constraint(self):
        is_valid, _ = validate_value_constraints(5, {'max': 10})
        self.assertTrue(is_valid)
        is_valid, _ = validate_value_constraints(15, {'max': 10})
        self.assertFalse(is_valid)

    def test_min_length_constraint(self):
        is_valid, _ = validate_value_constraints("hello", {'min_length': 3})
        self.assertTrue(is_valid)
        is_valid, _ = validate_value_constraints("hi", {'min_length': 3})
        self.assertFalse(is_valid)
        is_valid, _ = validate_value_constraints([1, 2, 3], {'min_length': 2})
        self.assertTrue(is_valid)

    def test_max_length_constraint(self):
        is_valid, _ = validate_value_constraints("hi", {'max_length': 5})
        self.assertTrue(is_valid)
        is_valid, _ = validate_value_constraints("hello world", {'max_length': 5})
        self.assertFalse(is_valid)

    def test_pattern_constraint(self):
        is_valid, _ = validate_value_constraints("2023-01-15", {'pattern': r'^\d{4}-\d{2}-\d{2}$'})
        self.assertTrue(is_valid)
        is_valid, _ = validate_value_constraints("01-15-2023", {'pattern': r'^\d{4}-\d{2}-\d{2}$'})
        self.assertFalse(is_valid)

    def test_enum_constraint(self):
        is_valid, _ = validate_value_constraints("gdelt", {'enum': ['gdelt', 'google_trends']})
        self.assertTrue(is_valid)
        is_valid, _ = validate_value_constraints("twitter", {'enum': ['gdelt', 'google_trends']})
        self.assertFalse(is_valid)


class TestRecordValidation(unittest.TestCase):
    """Tests for validate_record function."""

    def setUp(self):
        self.simple_schema = {
            'required': ['id', 'name'],
            'properties': {
                'id': {'type': 'integer'},
                'name': {'type': 'string'},
                'value': {'type': 'number', 'constraints': {'min': 0}}
            }
        }

    def test_valid_record(self):
        record = {'id': 1, 'name': 'test', 'value': 10}
        is_valid, errors = validate_record(record, self.simple_schema)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_missing_required_field(self):
        record = {'id': 1}
        is_valid, errors = validate_record(record, self.simple_schema)
        self.assertFalse(is_valid)
        self.assertTrue(any("Missing required field: name" in e for e in errors))

    def test_invalid_type(self):
        record = {'id': 'not an integer', 'name': 'test'}
        is_valid, errors = validate_record(record, self.simple_schema)
        self.assertFalse(is_valid)
        self.assertTrue(any("invalid type" in e for e in errors))

    def test_constraint_violation(self):
        record = {'id': 1, 'name': 'test', 'value': -5}
        is_valid, errors = validate_record(record, self.simple_schema)
        self.assertFalse(is_valid)
        self.assertTrue(any("less than minimum" in e for e in errors))

    def test_extra_fields_ignored(self):
        record = {'id': 1, 'name': 'test', 'extra_field': 'ignored'}
        is_valid, errors = validate_record(record, self.simple_schema)
        self.assertTrue(is_valid)


class TestSchemaLoading(unittest.TestCase):
    """Tests for load_schema function."""

    def test_load_valid_schema(self):
        schema_content = {
            'type': 'object',
            'properties': {'id': {'type': 'integer'}}
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(schema_content, f)
            temp_path = f.name

        try:
            # Change to temp directory to simulate project root
            original_dir = os.getcwd()
            os.chdir(os.path.dirname(temp_path))
            schema = load_schema(os.path.basename(temp_path))
            self.assertIsNotNone(schema)
            self.assertEqual(schema['type'], 'object')
        finally:
            os.chdir(original_dir)
            os.unlink(temp_path)

    def test_load_nonexistent_schema(self):
        schema = load_schema("nonexistent_file.yaml")
        self.assertIsNone(schema)


class TestDatasetFileValidation(unittest.TestCase):
    """Tests for validate_dataset_file function."""

    def setUp(self):
        self.test_schema = {
            'type': 'object',
            'required': ['id', 'name'],
            'properties': {
                'id': {'type': 'integer'},
                'name': {'type': 'string'}
            }
        }

    def test_validate_valid_csv(self):
        # Create temp schema file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(self.test_schema, f)
            schema_path = f.name

        # Create temp CSV file
        df = pd.DataFrame({'id': [1, 2, 3], 'name': ['a', 'b', 'c']})
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f, index=False)
            csv_path = f.name

        try:
            original_dir = os.getcwd()
            os.chdir(os.path.dirname(schema_path))
            is_valid, errors = validate_dataset_file(
                os.path.basename(csv_path),
                os.path.basename(schema_path)
            )
            self.assertTrue(is_valid)
            self.assertEqual(len(errors), 0)
        finally:
            os.chdir(original_dir)
            os.unlink(schema_path)
            os.unlink(csv_path)

    def test_validate_empty_csv(self):
        schema_content = {'type': 'object', 'properties': {}}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(schema_content, f)
            schema_path = f.name

        # Create empty CSV with only headers
        df = pd.DataFrame({'id': [], 'name': []})
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df.to_csv(f, index=False)
            csv_path = f.name

        try:
            original_dir = os.getcwd()
            os.chdir(os.path.dirname(schema_path))
            is_valid, errors = validate_dataset_file(
                os.path.basename(csv_path),
                os.path.basename(schema_path)
            )
            self.assertFalse(is_valid)
            self.assertTrue(any("empty" in e.lower() for e in errors))
        finally:
            os.chdir(original_dir)
            os.unlink(schema_path)
            os.unlink(csv_path)

    def test_validate_nonexistent_file(self):
        is_valid, errors = validate_dataset_file("nonexistent.csv", "schema.yaml")
        self.assertFalse(is_valid)
        self.assertTrue(any("not found" in e.lower() for e in errors))


if __name__ == '__main__':
    unittest.main()