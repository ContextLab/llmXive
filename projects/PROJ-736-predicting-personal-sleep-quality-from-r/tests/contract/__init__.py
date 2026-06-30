"""
Contract tests and schema definitions for the sleep quality prediction pipeline.

This module contains:
- YAML schema definitions for dataset and result validation
- Helper functions to load and validate JSON data against schemas
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any

# Schema file paths relative to tests/contract/
DATASET_SCHEMA_PATH = Path(__file__).parent / "dataset.schema.yaml"
RESULT_SCHEMA_PATH = Path(__file__).parent / "result.schema.yaml"

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema file."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_json_against_schema(json_path: Path, schema_path: Path) -> bool:
    """
    Validate a JSON file against a YAML schema.
    Note: This is a basic validation. For full schema validation,
    a library like jsonschema would be required.
    """
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        schema = load_schema(schema_path)
        
        # Basic structural checks based on schema properties
        if not isinstance(data, dict):
            return False
        
        # Check required top-level keys
        required_keys = schema.get('required', [])
        for key in required_keys:
            if key not in data:
                return False
        
        return True
    except Exception:
        return False
