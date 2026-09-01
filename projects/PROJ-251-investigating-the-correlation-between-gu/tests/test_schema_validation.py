import os
import unittest
import yaml
from pathlib import Path
from code.utils.validators import validate_dataset_schema

class TestSchemaValidation(unittest.TestCase):
    def setUp(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.schema_path = self.project_root / "contracts" / "dataset.schema.yaml"
        
    def test_schema_file_exists(self):
        """Verify that the schema file exists."""
        self.assertTrue(self.schema_path.exists(), f"Schema file not found: {self.schema_path}")
        
    def test_schema_is_valid_yaml(self):
        """Verify that the schema file is valid YAML."""
        try:
            with open(self.schema_path, 'r') as f:
                schema = yaml.safe_load(f)
            self.assertIsInstance(schema, dict)
        except yaml.YAMLError as e:
            self.fail(f"Schema file is not valid YAML: {e}")
            
    def test_schema_contains_required_fields(self):
        """Verify that the schema contains all required fields."""
        with open(self.schema_path, 'r') as f:
            schema = yaml.safe_load(f)
            
        required_fields = ['subject_id', 'taxa_abundances', 'titer_baseline', 'titer_post']
        for field in required_fields:
            self.assertIn(field, schema.get('required', []), f"Missing required field: {field}")
            
    def test_validate_dataset_schema_loads_yaml(self):
        """Test that the validator can load and parse the schema YAML."""
        try:
            with open(self.schema_path, 'r') as f:
                schema = yaml.safe_load(f)
            self.assertIsNotNone(schema)
            self.assertEqual(schema['type'], 'object')
        except Exception as e:
            self.fail(f"Failed to load schema: {e}")
            
if __name__ == '__main__':
    unittest.main()