"""
Contract tests for the Caco-2 dataset schema.

Validates that data produced by the retrieval and preprocessing pipeline
adheres to the schema defined in specs/001-molecular-flexibility-permeability/contracts/dataset.schema.yaml.

Specific test function: test_schema_compliance
"""
import json
import os
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path to allow imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SCHEMA_PATH = PROJECT_ROOT / "specs" / "001-molecular-flexibility-permeability" / "contracts" / "dataset.schema.yaml"
TEST_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "filtered_data.csv"

# Helper to load YAML without external dependency if possible, 
# but since requirements.txt includes pyvib and standard scientific stack, 
# we assume PyYAML is available or implement a simple parser for this specific schema.
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the JSON schema from the YAML file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        if HAS_YAML:
            return yaml.safe_load(f)
        else:
            # Fallback: Simple YAML parser for this specific structure if PyYAML missing
            # This is a minimal parser for the expected schema structure
            content = f.read()
            # Basic heuristic: if it looks like JSON (starts with {), load as JSON
            if content.strip().startswith('{'):
                return json.loads(content)
            else:
                raise ImportError("PyYAML is required to load the schema file.")


def validate_record(record: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate a single record against the schema.
    Returns a list of error messages.
    """
    errors = []
    properties = schema.get('properties', {})
    required_fields = schema.get('required', [])

    # Check required fields
    for field in required_fields:
        if field not in record or record[field] is None:
            errors.append(f"Missing required field: {field}")

    # Check field types and constraints
    for field, value in record.items():
        if field not in properties:
            # Allow extra fields? Schema usually implies strictness in contracts.
            # For now, we log a warning or ignore if not in schema.
            continue

        field_schema = properties[field]
        expected_type = field_schema.get('type')

        if expected_type == 'string':
            if not isinstance(value, str):
                errors.append(f"Field '{field}' should be string, got {type(value).__name__}")
            # Check minLength if present
            if 'minLength' in field_schema and len(value) < field_schema['minLength']:
                errors.append(f"Field '{field}' length {len(value)} < minLength {field_schema['minLength']}")
        
        elif expected_type == 'number':
            if not isinstance(value, (int, float)):
                errors.append(f"Field '{field}' should be number, got {type(value).__name__}")
            # Check minimum if present
            if 'minimum' in field_schema and value < field_schema['minimum']:
                errors.append(f"Field '{field}' value {value} < minimum {field_schema['minimum']}")
        
        elif expected_type == 'object':
            if not isinstance(value, dict):
                errors.append(f"Field '{field}' should be object, got {type(value).__name__}")
            else:
                # Validate nested properties if defined
                nested_props = field_schema.get('properties', {})
                nested_required = field_schema.get('required', [])
                for nested_field in nested_required:
                    if nested_field not in value:
                        errors.append(f"Missing nested required field in '{field}': {nested_field}")
                for nested_field, nested_val in value.items():
                    if nested_field in nested_props:
                        nested_schema = nested_props[nested_field]
                        nested_type = nested_schema.get('type')
                        if nested_type == 'string' and not isinstance(nested_val, str):
                            errors.append(f"Nested field '{field}.{nested_field}' should be string")
                        elif nested_type == 'number' and not isinstance(nested_val, (int, float)):
                            errors.append(f"Nested field '{field}.{nested_field}' should be number")

    return errors


class TestDatasetSchema(unittest.TestCase):
    """
    Contract tests for the Caco-2 dataset schema compliance.
    """

    @classmethod
    def setUpClass(cls):
        """Load schema and test data once for all tests."""
        if not SCHEMA_PATH.exists():
            raise FileNotFoundError(
                f"Schema file missing at {SCHEMA_PATH}. "
                "Ensure task T007 has been completed successfully."
            )
        cls.schema = load_schema(SCHEMA_PATH)
        
        if not TEST_DATA_PATH.exists():
            # If data doesn't exist yet, we skip the data validation tests
            # but we can still test that the schema loads correctly.
            cls.data = []
            cls.has_data = False
        else:
            import pandas as pd
            df = pd.read_csv(TEST_DATA_PATH)
            cls.data = df.to_dict(orient='records')
            cls.has_data = True

    def test_schema_exists(self):
        """Verify the schema file is valid and loadable."""
        self.assertIsNotNone(self.schema)
        self.assertIn('properties', self.schema)
        self.assertIn('required', self.schema)

    def test_schema_compliance(self):
        """
        Validates data against the schema defined in T007.
        
        Requirement: Implement specific test function: 
        tests/contract/test_dataset.py::test_schema_compliance 
        (validates data against the schema defined in T007).
        """
        if not self.has_data:
            self.skipTest("No test data found at data/processed/filtered_data.csv. "
                          "Run retrieval and preprocessing tasks first.")

        total_records = len(self.data)
        failed_records = []
        error_details = []

        for idx, record in enumerate(self.data):
            record_errors = validate_record(record, self.schema)
            if record_errors:
                failed_records.append(idx)
                error_details.append({
                    "row": idx,
                    "errors": record_errors
                })

        if failed_records:
            error_summary = f"Schema validation failed for {len(failed_records)} records.\n"
            for detail in error_details[:5]: # Show first 5 errors
                error_summary += f"  Row {detail['row']}: {detail['errors']}\n"
            if len(error_details) > 5:
                error_summary += f"  ... and {len(error_details) - 5} more."
            
            self.fail(error_summary)

        # If we reach here, all records passed
        self.assertEqual(len(failed_records), 0, 
                         f"Schema validation failed for {len(failed_records)} records.")
        
        # Additional specific checks based on T007 requirements
        # T007 requires: smiles, logPapp, mw, psa, assay_id, protocol_metadata
        required_top_level = ['smiles', 'logPapp', 'mw', 'psa', 'assay_id', 'protocol_metadata']
        for field in required_top_level:
            self.assertIn(field, self.schema['properties'], 
                          f"Schema missing required field: {field}")

        # Check protocol_metadata structure
        if 'protocol_metadata' in self.schema['properties']:
            meta_schema = self.schema['properties']['protocol_metadata']
            meta_required = meta_schema.get('required', [])
            expected_meta = ['lab_id', 'temperature', 'passage']
            for exp in expected_meta:
                self.assertIn(exp, meta_required, 
                              f"protocol_metadata missing required field: {exp}")


if __name__ == '__main__':
    unittest.main()
