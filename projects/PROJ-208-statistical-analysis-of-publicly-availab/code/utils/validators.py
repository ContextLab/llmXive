"""
Schema validators for llmXive pipeline.

Implements SC-001: Dataset schema validation against contracts.
"""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json
import yaml
import re

class ValidationError(Exception):
    """Raised when schema validation fails."""
    pass

class SchemaValidator:
    """Validates data against JSON schemas defined in contracts/."""
    
    def __init__(self, contracts_dir: Path):
        self.contracts_dir = Path(contracts_dir)
        if not self.contracts_dir.exists():
            raise FileNotFoundError(f"Contracts directory not found: {self.contracts_dir}")
    
    def load_schema(self, schema_name: str) -> Dict[str, Any]:
        """Load a schema from contracts directory."""
        schema_path = self.contracts_dir / f"{schema_name}.yaml"
        if not schema_path.exists():
            schema_path = self.contracts_dir / f"{schema_name}.json"
        
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema not found: {schema_path}")
        
        with open(schema_path, 'r') as f:
            if schema_path.suffix == '.yaml':
                return yaml.safe_load(f)
            else:
                return json.load(f)
    
    def validate(self, data: Dict[str, Any], schema_name: str) -> Tuple[bool, List[str]]:
        """
        Validate data against a schema.
        
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        schema = self.load_schema(schema_name)
        errors = []
        
        # Check required fields
        required_fields = schema.get('required', [])
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        # Validate field types
        properties = schema.get('properties', {})
        for field, value in data.items():
            if field in properties:
                expected_type = properties[field].get('type')
                if expected_type == 'string' and not isinstance(value, str):
                    errors.append(f"Field '{field}' should be string, got {type(value).__name__}")
                elif expected_type == 'number' and not isinstance(value, (int, float)):
                    errors.append(f"Field '{field}' should be number, got {type(value).__name__}")
                elif expected_type == 'integer' and not isinstance(value, int):
                    errors.append(f"Field '{field}' should be integer, got {type(value).__name__}")
                elif expected_type == 'boolean' and not isinstance(value, bool):
                    errors.append(f"Field '{field}' should be boolean, got {type(value).__name__}")
                elif expected_type == 'array' and not isinstance(value, list):
                    errors.append(f"Field '{field}' should be array, got {type(value).__name__}")
                elif expected_type == 'object' and not isinstance(value, dict):
                    errors.append(f"Field '{field}' should be object, got {type(value).__name__}")
        
        return len(errors) == 0, errors

def ensure_contracts_dir(project_root: Path) -> Path:
    """Ensure contracts directory exists and return its path."""
    contracts_dir = project_root / "contracts"
    contracts_dir.mkdir(parents=True, exist_ok=True)
    return contracts_dir

def load_schema(contracts_dir: Path, schema_name: str) -> Dict[str, Any]:
    """Load a schema from contracts directory."""
    validator = SchemaValidator(contracts_dir)
    return validator.load_schema(schema_name)

def get_validator(project_root: Path) -> SchemaValidator:
    """Get a schema validator for the project."""
    contracts_dir = project_root / "contracts"
    return SchemaValidator(contracts_dir)

def validate_dataset_schema(data: Dict[str, Any], contracts_dir: Path) -> Tuple[bool, List[str]]:
    """Validate dataset against its schema."""
    validator = SchemaValidator(contracts_dir)
    return validator.validate(data, 'dataset_schema')
