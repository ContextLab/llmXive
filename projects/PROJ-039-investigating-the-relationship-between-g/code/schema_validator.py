"""
Schema validation module for the Gut Microbiome - EEG Alpha Power project.
Validates data against contracts/dataset.schema.yaml and contracts/output.schema.yaml.
"""
import os
import sys
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Attempt to import jsonschema, fallback to basic validation if missing
try:
    import jsonschema
    from jsonschema import validate, ValidationError, Draft7Validator
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    logging.warning("jsonschema library not found. Using basic type checking only.")

from config import get_project_root

logger = logging.getLogger(__name__)

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a JSON/YAML schema file."""
    full_path = Path(get_project_root()) / schema_path
    if not full_path.exists():
        raise FileNotFoundError(f"Schema file not found: {full_path}")
    
    with open(full_path, 'r') as f:
        if full_path.suffix in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        else:
            return json.load(f)

class SchemaValidator:
    """Validates data dictionaries or JSON files against a loaded schema."""
    
    def __init__(self, schema_path: str):
        self.schema = load_schema(schema_path)
        self.validator = None
        if HAS_JSONSCHEMA:
            self.validator = Draft7Validator(self.schema)
    
    def validate_dict(self, data: Dict[str, Any]) -> bool:
        """Validate a dictionary against the schema."""
        if not HAS_JSONSCHEMA:
            # Basic manual validation fallback
            return self._basic_validate(data)
        
        errors = list(self.validator.iter_errors(data))
        if errors:
            for error in errors:
                logger.error(f"Schema validation error: {error.message} at path: {'/'.join(map(str, error.path))}")
            return False
        return True

    def _basic_validate(self, data: Dict[str, Any]) -> bool:
        """Fallback basic validation if jsonschema is missing."""
        # Check required fields
        required = self.schema.get('required', [])
        for field in required:
            if field not in data:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Check types for known fields
        properties = self.schema.get('properties', {})
        for key, value in data.items():
            if key in properties:
                expected_type = properties[key].get('type')
                if expected_type == 'integer' and not isinstance(value, int):
                    logger.error(f"Field {key} expected integer, got {type(value)}")
                    return False
                if expected_type == 'number' and not isinstance(value, (int, float)):
                    logger.error(f"Field {key} expected number, got {type(value)}")
                    return False
                if expected_type == 'string' and not isinstance(value, str):
                    logger.error(f"Field {key} expected string, got {type(value)}")
                    return False
        return True

    def validate_file(self, file_path: str) -> bool:
        """Validate a JSON file against the schema."""
        full_path = Path(get_project_root()) / file_path
        if not full_path.exists():
            raise FileNotFoundError(f"Data file not found: {full_path}")
        
        with open(full_path, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON file: {e}")
                return False
        
        return self.validate_dict(data)

def main():
    """CLI entry point for schema validation."""
    import argparse
    parser = argparse.ArgumentParser(description="Validate data files against project schemas.")
    parser.add_argument('--schema', type=str, required=True, help='Path to schema file (e.g., contracts/dataset.schema.yaml)')
    parser.add_argument('--data', type=str, required=True, help='Path to data file (JSON) or directory of JSON files')
    args = parser.parse_args()

    validator = SchemaValidator(args.schema)
    
    data_path = Path(get_project_root()) / args.data
    if data_path.is_file():
        if validator.validate_file(args.data):
            logger.info(f"Validation passed for {args.data}")
            sys.exit(0)
        else:
            logger.error(f"Validation failed for {args.data}")
            sys.exit(1)
    elif data_path.is_dir():
        all_valid = True
        for file_path in data_path.glob('*.json'):
            rel_path = str(file_path.relative_to(get_project_root()))
            if not validator.validate_file(rel_path):
                all_valid = False
        if all_valid:
            logger.info("All JSON files in directory passed validation.")
            sys.exit(0)
        else:
            logger.error("Some JSON files failed validation.")
            sys.exit(1)
    else:
        logger.error(f"Path does not exist: {args.data}")
        sys.exit(1)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
