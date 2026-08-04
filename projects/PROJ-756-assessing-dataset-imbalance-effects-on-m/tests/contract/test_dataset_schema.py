"""
Contract test for data schema validation.

Validates that processed datasets in data/processed/ conform to
the schema defined in contracts/dataset.schema.yaml.

This test ensures data integrity before training and evaluation steps.
"""
import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import unittest

import pandas as pd
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the JSON schema from YAML file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)


def validate_type(value: Any, expected_type: str, field_path: str) -> bool:
    """Validate that a value matches the expected JSON schema type."""
    type_map = {
        'string': str,
        'integer': int,
        'number': (int, float),
        'boolean': bool,
        'array': list,
        'object': dict,
        'null': type(None)
    }
    
    expected_python_type = type_map.get(expected_type)
    if expected_python_type is None:
        logger.warning(f"Unknown type '{expected_type}' for field {field_path}")
        return False
    
    return isinstance(value, expected_python_type)


def validate_constraints(value: Any, constraints: Dict[str, Any], field_path: str) -> bool:
    """Validate numeric and other constraints defined in the schema."""
    valid = True
    
    if 'minimum' in constraints:
        if not isinstance(value, (int, float)) or value < constraints['minimum']:
            logger.error(f"Field {field_path} value {value} is below minimum {constraints['minimum']}")
            valid = False
    
    if 'maximum' in constraints:
        if not isinstance(value, (int, float)) or value > constraints['maximum']:
            logger.error(f"Field {field_path} value {value} exceeds maximum {constraints['maximum']}")
            valid = False
    
    if 'enum' in constraints:
        if value not in constraints['enum']:
            logger.error(f"Field {field_path} value '{value}' not in allowed enum {constraints['enum']}")
            valid = False
    
    return valid


def validate_object(data: Dict[str, Any], schema: Dict[str, Any], path: str = "root") -> bool:
    """Recursively validate an object against its schema definition."""
    valid = True
    
    # Check required fields
    if 'required' in schema:
        for field in schema['required']:
            if field not in data:
                logger.error(f"Missing required field: {path}.{field}")
                valid = False
            else:
                # Validate the field
                field_schema = schema['properties'].get(field, {})
                if not validate_field(data[field], field_schema, f"{path}.{field}"):
                    valid = False
    
    # Check additional properties
    if 'additionalProperties' in schema and schema['additionalProperties'] is False:
        allowed_keys = set(schema.get('properties', {}).keys())
        for key in data.keys():
            if key not in allowed_keys:
                logger.warning(f"Unexpected additional property found: {path}.{key}")
    
    return valid


def validate_field(value: Any, field_schema: Dict[str, Any], path: str) -> bool:
    """Validate a single field against its schema definition."""
    valid = True
    
    # Check type
    if 'type' in field_schema:
        if not validate_type(value, field_schema['type'], path):
            logger.error(f"Type mismatch for {path}: expected {field_schema['type']}, got {type(value).__name__}")
            valid = False
        else:
            # If type matches, check constraints
            if not validate_constraints(value, field_schema, path):
                valid = False
    
    # Check array items
    if field_schema.get('type') == 'array' and isinstance(value, list):
        items_schema = field_schema.get('items', {})
        for i, item in enumerate(value):
            if not validate_field(item, items_schema, f"{path}[{i}]"):
                valid = False
    
    # Check object properties
    if field_schema.get('type') == 'object' and isinstance(value, dict):
        if not validate_object(value, field_schema, path):
            valid = False
    
    return valid


def load_processed_dataset(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a processed dataset JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON in {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return None


class TestDatasetSchema(unittest.TestCase):
    """Contract tests for dataset schema validation."""

    @classmethod
    def setUpClass(cls):
        """Load the schema once for all tests."""
        logger.info("Loading schema from %s", SCHEMA_PATH)
        cls.schema = load_schema(SCHEMA_PATH)
        logger.info("Schema loaded successfully")

    def test_schema_file_exists(self):
        """Verify the schema file exists."""
        self.assertTrue(SCHEMA_PATH.exists(), "Schema file must exist")

    def test_processed_data_directory_exists(self):
        """Verify the processed data directory exists."""
        self.assertTrue(PROCESSED_DATA_DIR.exists(), "Processed data directory must exist")

    def test_all_processed_files_valid(self):
        """Validate all JSON files in data/processed/ against the schema."""
        if not PROCESSED_DATA_DIR.exists():
            self.skipTest("Processed data directory does not exist")
        
        json_files = list(PROCESSED_DATA_DIR.glob("*.json"))
        
        self.assertGreater(len(json_files), 0, "No processed JSON files found in data/processed/")
        
        all_valid = True
        for file_path in json_files:
            logger.info(f"Validating {file_path.name}...")
            data = load_processed_dataset(file_path)
            
            if data is None:
                logger.error(f"Failed to load {file_path.name}")
                all_valid = False
                continue
            
            if not validate_object(data, self.schema, file_path.name):
                logger.error(f"Schema validation failed for {file_path.name}")
                all_valid = False
            else:
                logger.info(f"✓ {file_path.name} passed schema validation")
        
        self.assertTrue(all_valid, "One or more processed files failed schema validation")

    def test_metadata_structure(self):
        """Test that metadata section follows the expected structure."""
        json_files = list(PROCESSED_DATA_DIR.glob("*.json"))
        if not json_files:
            self.skipTest("No processed files to test")
        
        for file_path in json_files:
            data = load_processed_dataset(file_path)
            if not data:
                continue
            
            if 'metadata' not in data:
                self.fail(f"Missing 'metadata' in {file_path.name}")
            
            metadata = data['metadata']
            self.assertIn('source', metadata, f"Missing 'source' in {file_path.name}")
            self.assertIn('timestamp', metadata, f"Missing 'timestamp' in {file_path.name}")
            self.assertIn('sample_count', metadata, f"Missing 'sample_count' in {file_path.name}")
            self.assertIn('property_name', metadata, f"Missing 'property_name' in {file_path.name}")
            
            # Validate types
            self.assertIsInstance(metadata['source'], str, f"'source' must be string in {file_path.name}")
            self.assertIsInstance(metadata['timestamp'], str, f"'timestamp' must be string in {file_path.name}")
            self.assertIsInstance(metadata['sample_count'], int, f"'sample_count' must be int in {file_path.name}")
            self.assertGreater(metadata['sample_count'], 0, f"'sample_count' must be > 0 in {file_path.name}")

    def test_imbalance_scores_present(self):
        """Test that imbalance scores are present and valid."""
        json_files = list(PROCESSED_DATA_DIR.glob("*.json"))
        if not json_files:
            self.skipTest("No processed files to test")
        
        for file_path in json_files:
            data = load_processed_dataset(file_path)
            if not data:
                continue
            
            if 'imbalance_scores' not in data:
                self.fail(f"Missing 'imbalance_scores' in {file_path.name}")
            
            scores = data['imbalance_scores']
            self.assertIn('target_gini', scores, f"Missing 'target_gini' in {file_path.name}")
            self.assertIn('compositional_gini', scores, f"Missing 'compositional_gini' in {file_path.name}")
            
            # Validate Gini coefficient range [0, 1]
            target_gini = scores['target_gini']
            compositional_gini = scores['compositional_gini']
            
            self.assertGreaterEqual(target_gini, 0, f"'target_gini' must be >= 0 in {file_path.name}")
            self.assertLessEqual(target_gini, 1, f"'target_gini' must be <= 1 in {file_path.name}")
            self.assertGreaterEqual(compositional_gini, 0, f"'compositional_gini' must be >= 0 in {file_path.name}")
            self.assertLessEqual(compositional_gini, 1, f"'compositional_gini' must be <= 1 in {file_path.name}")


if __name__ == '__main__':
    unittest.main(verbosity=2)