"""
Unit tests for validate_outputs.py (T028).
"""
import os
import sys
import csv
import json
import tempfile
import unittest
from pathlib import Path

# Add project root to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.validate_outputs import (
    validate_csv_schema,
    validate_json_schema,
    validate_png_file,
    validate_success_criteria
)


class TestValidateCSV(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.schema = {
            "required_columns": ["id", "value"],
            "column_types": {"value": "float"}
        }

    def tearDown(self):
        # Cleanup temp files
        for f in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, f))
        os.rmdir(self.temp_dir)

    def test_valid_csv(self):
        path = os.path.join(self.temp_dir, "valid.csv")
        with open(path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["id", "value"])
            writer.writeheader()
            writer.writerow({"id": "1", "value": "1.5"})
        
        valid, errors = validate_csv_schema(path, self.schema)
        self.assertTrue(valid)
        self.assertEqual(errors, [])

    def test_missing_column(self):
        path = os.path.join(self.temp_dir, "missing_col.csv")
        with open(path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["id"])
            writer.writeheader()
            writer.writerow({"id": "1"})
        
        valid, errors = validate_csv_schema(path, self.schema)
        self.assertFalse(valid)
        self.assertIn("Missing required columns", str(errors))

    def test_invalid_type(self):
        path = os.path.join(self.temp_dir, "bad_type.csv")
        with open(path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["id", "value"])
            writer.writeheader()
            writer.writerow({"id": "1", "value": "not_a_float"})
        
        valid, errors = validate_csv_schema(path, self.schema)
        self.assertFalse(valid)
        self.assertTrue(any("expected float" in str(e) for e in errors))


class TestValidateJSON(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.schema = {
            "required_keys": ["result", "status"],
            "key_types": {"result": "float"}
        }

    def tearDown(self):
        for f in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, f))
        os.rmdir(self.temp_dir)

    def test_valid_json(self):
        path = os.path.join(self.temp_dir, "valid.json")
        with open(path, 'w') as f:
            json.dump({"result": 0.85, "status": "ok"}, f)
        
        valid, errors = validate_json_schema(path, self.schema)
        self.assertTrue(valid)
        self.assertEqual(errors, [])

    def test_missing_key(self):
        path = os.path.join(self.temp_dir, "missing_key.json")
        with open(path, 'w') as f:
            json.dump({"result": 0.85}, f)
        
        valid, errors = validate_json_schema(path, self.schema)
        self.assertFalse(valid)
        self.assertIn("Missing required keys", str(errors))

    def test_invalid_type(self):
        path = os.path.join(self.temp_dir, "bad_type.json")
        with open(path, 'w') as f:
            json.dump({"result": "string", "status": "ok"}, f)
        
        valid, errors = validate_json_schema(path, self.schema)
        self.assertFalse(valid)
        self.assertTrue(any("expected float" in str(e) for e in errors))


class TestValidatePNG(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        for f in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, f))
        os.rmdir(self.temp_dir)

    def test_valid_png_header(self):
        path = os.path.join(self.temp_dir, "fake.png")
        # Write valid PNG header + some dummy data
        with open(path, 'wb') as f:
            f.write(b'\x89PNG\r\n\x1a\n')
            f.write(b'x' * 100)
        
        valid, errors = validate_png_file(path)
        self.assertTrue(valid)
        self.assertEqual(errors, [])

    def test_invalid_header(self):
        path = os.path.join(self.temp_dir, "fake.jpg")
        with open(path, 'wb') as f:
            f.write(b'JPG HEADER')
        
        valid, errors = validate_png_file(path)
        self.assertFalse(valid)
        self.assertTrue(any("not a valid PNG" in str(e) for e in errors))

    def test_file_not_found(self):
        valid, errors = validate_png_file("/nonexistent/file.png")
        self.assertFalse(valid)
        self.assertTrue(any("not found" in str(e) for e in errors))


class TestValidateSuccessCriteria(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        for f in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, f))
        os.rmdir(self.temp_dir)

    def test_csv_correlation_range(self):
        path = os.path.join(self.temp_dir, "results.csv")
        with open(path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["interaction_id", "correlation_coefficient"])
            writer.writeheader()
            writer.writerow({"interaction_id": "1", "correlation_coefficient": "0.5"})
        
        valid, errors = validate_success_criteria(path, {"correlation_range": (-1.0, 1.0)})
        self.assertTrue(valid)
        
        # Test invalid range
        with open(path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["interaction_id", "correlation_coefficient"])
            writer.writeheader()
            writer.writerow({"interaction_id": "1", "correlation_coefficient": "1.5"})
        
        valid, errors = validate_success_criteria(path, {"correlation_range": (-1.0, 1.0)})
        self.assertFalse(valid)
        self.assertTrue(any("out of range" in str(e) for e in errors))


if __name__ == '__main__':
    unittest.main()