import os
import unittest
import yaml
from pathlib import Path

class TestSchemaGeneration(unittest.TestCase):
    def test_schema_file_exists(self):
        """Verify that the dataset schema file exists at the expected path."""
        schema_path = Path("specs/001-investigating-the-correlation-between-gu/contracts/dataset.schema.yaml")
        self.assertTrue(schema_path.exists(), f"Schema file missing: {schema_path}")

    def test_schema_is_valid_yaml(self):
        """Verify that the schema file contains valid YAML."""
        schema_path = Path("specs/001-investigating-the-correlation-between-gu/contracts/dataset.schema.yaml")
        try:
            with open(schema_path, 'r') as f:
                data = yaml.safe_load(f)
            self.assertIsInstance(data, dict)
        except yaml.YAMLError as e:
            self.fail(f"Schema file is not valid YAML: {e}")

    def test_schema_has_required_structure(self):
        """Verify that the schema contains the required top-level keys."""
        schema_path = Path("specs/001-investigating-the-correlation-between-gu/contracts/dataset.schema.yaml")
        with open(schema_path, 'r') as f:
            data = yaml.safe_load(f)
        
        self.assertIn('type', data)
        self.assertEqual(data['type'], 'object')
        self.assertIn('required', data)
        self.assertIn('properties', data)
        
        required_fields = data.get('required', [])
        self.assertIn('subject_id', required_fields)
        self.assertIn('titer_baseline', required_fields)
        self.assertIn('titer_post', required_fields)

        properties = data.get('properties', {})
        self.assertIn('subject_id', properties)
        self.assertIn('titer_baseline', properties)
        self.assertIn('titer_post', properties)
        self.assertIn('shannon_diversity', properties)
        self.assertIn('log_titer', properties)
        self.assertIn('additionalProperties', properties)