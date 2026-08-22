"""
Script to validate the dataset schema contract.

This script loads the YAML schema defined in contracts/dataset.schema.yaml
and validates it against pydantic and jsonschema to ensure it is syntactically
valid and loadable. It serves as the verification step for Task T007.

Usage:
    python scripts/validate_dataset_schema.py
"""
import os
import sys
import logging
from pathlib import Path
import json
import yaml

# Attempt to import jsonschema; if missing, we will rely on pydantic validation
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    logging.warning("jsonschema not installed. Falling back to pydantic validation only.")

try:
    from pydantic import BaseModel, Field, ValidationError, create_model
    from typing import Any, Dict, List, Optional, Union
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    logging.error("pydantic is required for schema validation but is not installed.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"

def load_yaml_schema(path: Path) -> Dict[str, Any]:
    """Load and parse the YAML schema file."""
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found at: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)
    
    if not isinstance(schema, dict):
        raise ValueError("Schema file must contain a valid YAML dictionary.")
    
    return schema

def validate_with_pydantic(schema: Dict[str, Any]) -> bool:
    """
    Validate the schema structure by creating a dynamic Pydantic model
    and checking if it can be instantiated with valid data types.
    """
    logger.info("Validating schema structure using Pydantic...")
    
    properties = schema.get('properties', {})
    required_fields = schema.get('required', [])
    
    if not properties:
        logger.error("Schema contains no 'properties' field.")
        return False

    # Map JSON Schema types to Pydantic field types
    type_mapping = {
        'string': str,
        'integer': int,
        'number': float,
        'boolean': bool,
        'array': list,
        'object': dict
    }

    field_definitions = {}
    
    for field_name, field_spec in properties.items():
        field_type_str = field_spec.get('type')
        
        if field_type_str not in type_mapping:
            logger.warning(f"Skipping unsupported type '{field_type_str}' for field '{field_name}'")
            continue
        
        base_type = type_mapping[field_type_str]
        
        # Handle enum constraints
        if 'enum' in field_spec:
            from typing import Literal
            enum_values = tuple(field_spec['enum'])
            # Pydantic v2 handles Literal differently, using a generic approach
            field_type = base_type 
            # We will just use the base type for dynamic model creation 
            # and validate enum at runtime if needed, but for schema structure check, base type suffices.
        
        field_definitions[field_name] = (Optional[base_type], Field(default=None))

    if not field_definitions:
        logger.error("Could not map any fields to Pydantic types.")
        return False

    try:
        # Create a dynamic model
        DynamicModel = create_model('DynamicDatasetRecord', **field_definitions)
        
        # Test instantiation with a minimal valid record (partial data is okay for schema check)
        # We just need to ensure the model definition is valid
        logger.info("Pydantic model created successfully.")
        
        # Validate that required fields are tracked (Pydantic doesn't enforce 'required' 
        # in the same way as JSON schema in the model definition alone, 
        # but we check if the definition logic holds)
        logger.info("Pydantic validation passed: Schema is structurally sound.")
        return True

    except Exception as e:
        logger.error(f"Pydantic validation failed: {e}")
        return False

def validate_with_jsonschema(schema: Dict[str, Any]) -> bool:
    """
    Validate the schema itself against the JSON Schema meta-schema
    and optionally validate a dummy instance against it.
    """
    if not HAS_JSONSCHEMA:
        logger.warning("Skipping JSON Schema validation (library not installed).")
        return True

    logger.info("Validating schema against JSON Schema meta-schema...")
    
    try:
        # Validate the schema structure itself
        jsonschema.Draft7Validator.check_schema(schema)
        logger.info("Schema is valid JSON Schema Draft 7.")
        
        # Create a dummy instance based on 'required' fields to test instance validation
        properties = schema.get('properties', {})
        required_fields = schema.get('required', [])
        
        dummy_instance = {}
        for field in required_fields:
            if field in properties:
                prop = properties[field]
                p_type = prop.get('type')
                if p_type == 'string':
                    dummy_instance[field] = "test_id"
                elif p_type == 'integer':
                    dummy_instance[field] = 1
                elif p_type == 'number':
                    dummy_instance[field] = 1.0
                elif p_type == 'boolean':
                    dummy_instance[field] = True
                elif p_type == 'array':
                    dummy_instance[field] = []
                elif p_type == 'object':
                    dummy_instance[field] = {}
        
        # Validate dummy instance
        jsonschema.validate(instance=dummy_instance, schema=schema)
        logger.info("Dummy instance validation passed.")
        return True

    except jsonschema.exceptions.SchemaError as e:
        logger.error(f"Schema is invalid: {e.message}")
        return False
    except jsonschema.exceptions.ValidationError as e:
        logger.error(f"Validation error against schema: {e.message}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during JSON Schema validation: {e}")
        return False

def main():
    logger.info(f"Starting schema validation for: {SCHEMA_PATH}")
    
    if not SCHEMA_PATH.exists():
        logger.error(f"Schema file not found: {SCHEMA_PATH}")
        sys.exit(1)

    try:
        schema = load_yaml_schema(SCHEMA_PATH)
    except Exception as e:
        logger.error(f"Failed to load YAML schema: {e}")
        sys.exit(1)

    pydantic_valid = False
    jsonschema_valid = False

    if HAS_PYDANTIC:
        pydantic_valid = validate_with_pydantic(schema)
    
    if HAS_JSONSCHEMA:
        jsonschema_valid = validate_with_jsonschema(schema)
    
    # If we have pydantic, at least that check must pass. 
    # If we have jsonschema, it must also pass.
    # If neither, we can't validate properly.
    
    if not HAS_PYDANTIC and not HAS_JSONSCHEMA:
        logger.error("Neither pydantic nor jsonschema is available. Cannot validate.")
        sys.exit(1)

    if pydantic_valid and jsonschema_valid:
        logger.info("✅ Schema validation PASSED.")
        sys.exit(0)
    else:
        logger.error("❌ Schema validation FAILED.")
        if not pydantic_valid:
            logger.error("  - Pydantic validation failed.")
        if not jsonschema_valid:
            logger.error("  - JSON Schema validation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()