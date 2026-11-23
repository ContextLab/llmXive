"""
Contract tests for the Caco-2 dataset against the defined JSON schema.
These tests ensure data integrity and schema compliance as per FR-010 and T007.
"""
import json
import os
import sys
import unittest
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

# Schema path relative to project root
SCHEMA_PATH = "specs/001-molecular-flexibility-permeability/contracts/dataset.schema.yaml"

def load_yaml_schema(schema_path: Path) -> dict:
    """Load the JSON schema from a YAML file."""
    try:
        import yaml
        with open(schema_path, 'r') as f:
            return yaml.safe_load(f)
    except ImportError:
        # Fallback if PyYAML is not installed, though it should be in requirements
        raise RuntimeError("PyYAML is required to load schema files.")
    except FileNotFoundError:
        raise FileNotFoundError(f"Schema file not found at: {schema_path}")

def validate_against_schema(data: dict, schema: dict) -> list:
    """
    Basic validation of data against a JSON schema.
    Since jsonschema might not be installed, we implement a lightweight checker
    for the specific requirements of this task.
    """
    errors = []
    
    # Check required top-level keys
    required_fields = schema.get('required', [])
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    # Check property types if defined
    properties = schema.get('properties', {})
    for field, spec in properties.items():
        if field in data:
            value = data[field]
            expected_type = spec.get('type')
            
            if expected_type == 'string':
                if not isinstance(value, str):
                    errors.append(f"Field '{field}' must be string, got {type(value).__name__}")
            elif expected_type == 'number':
                if not isinstance(value, (int, float)):
                    errors.append(f"Field '{field}' must be number, got {type(value).__name__}")
            elif expected_type == 'object':
                if not isinstance(value, dict):
                    errors.append(f"Field '{field}' must be object, got {type(value).__name__}")
                # Check nested properties for protocol_metadata
                if field == 'protocol_metadata' and 'properties' in spec:
                    nested_props = spec['properties']
                    for nested_key, nested_spec in nested_props.items():
                        if nested_key in value:
                            nested_val = value[nested_key]
                            nested_type = nested_spec.get('type')
                            if nested_type == 'string' and not isinstance(nested_val, str):
                                errors.append(f"Nested field '{field}.{nested_key}' must be string")
    
    return errors

class TestDatasetSchemaCompliance(unittest.TestCase):
    """
    Test suite to validate the dataset schema defined in T007.
    """

    def setUp(self):
        """
        Ensure the schema file exists before running tests.
        """
        schema_file = project_root / SCHEMA_PATH
        if not schema_file.exists():
            self.fail(f"Schema file missing: {schema_file}. "
                      "Ensure T007 has been completed successfully.")
        self.schema = load_yaml_schema(schema_file)

    def test_schema_compliance(self):
        """
        Validates that the schema file is well-formed and contains the required
        definitions for the Caco-2 dataset as specified in T007.
        
        Requirements:
        - Fields: smiles (string), logPapp (number), mw (number), psa (number),
          assay_id (string), protocol_metadata (object).
        - protocol_metadata must contain standard_type (string).
        """
        # 1. Verify schema structure
        self.assertIn('type', self.schema, "Schema must define a top-level type")
        self.assertEqual(self.schema['type'], 'object', "Schema type must be 'object'")

        properties = self.schema.get('properties', {})
        self.assertIn('smiles', properties, "Schema must define 'smiles' property")
        self.assertIn('logPapp', properties, "Schema must define 'logPapp' property")
        self.assertIn('mw', properties, "Schema must define 'mw' property")
        self.assertIn('psa', properties, "Schema must define 'psa' property")
        self.assertIn('assay_id', properties, "Schema must define 'assay_id' property")
        self.assertIn('protocol_metadata', properties, "Schema must define 'protocol_metadata' property")

        # 2. Verify types
        self.assertEqual(properties['smiles']['type'], 'string')
        self.assertEqual(properties['logPapp']['type'], 'number')
        self.assertEqual(properties['mw']['type'], 'number')
        self.assertEqual(properties['psa']['type'], 'number')
        self.assertEqual(properties['assay_id']['type'], 'string')
        
        # Verify protocol_metadata structure
        pm_props = properties['protocol_metadata'].get('properties', {})
        self.assertIn('standard_type', pm_props, "protocol_metadata must contain 'standard_type'")
        self.assertEqual(pm_props['standard_type']['type'], 'string')

        # 3. Verify required fields
        required = self.schema.get('required', [])
        self.assertIn('smiles', required)
        self.assertIn('logPapp', required)
        self.assertIn('assay_id', required)
        self.assertIn('protocol_metadata', required)

        # 4. If processed data exists, validate a sample row against the schema
        processed_data_path = project_root / "data/processed/filtered_data.csv"
        if processed_data_path.exists():
            import pandas as pd
            df = pd.read_csv(processed_data_path)
            if len(df) > 0:
                # Check first row
                row = df.iloc[0].to_dict()
                # Handle JSON string in protocol_metadata if saved as string
                if 'protocol_metadata' in row and isinstance(row['protocol_metadata'], str):
                    try:
                        row['protocol_metadata'] = json.loads(row['protocol_metadata'])
                    except json.JSONDecodeError:
                        pass # Will fail validation below, which is expected if data is malformed
                
                errors = validate_against_schema(row, self.schema)
                self.assertEqual(len(errors), 0, f"First row of filtered_data.csv failed schema validation: {errors}")

    def test_schema_exists_and_valid(self):
        """
        A specific check to ensure the schema file is not empty and parses correctly.
        """
        self.assertIsNotNone(self.schema)
        self.assertIsInstance(self.schema, dict)

if __name__ == '__main__':
    unittest.main()