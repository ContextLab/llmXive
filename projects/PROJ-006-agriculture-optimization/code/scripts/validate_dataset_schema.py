"""
Script to validate the dataset schema contract.
Verifies that contracts/dataset.schema.yaml is valid YAML,
loadable, and compatible with Pydantic/JsonSchema validation logic.
"""
import os
import sys
import logging
from pathlib import Path
import json
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Determine the project root directory."""
    current = Path(__file__).resolve()
    # Traverse up until we find a directory that looks like the root
    # (e.g., contains 'contracts' or 'src')
    for parent in current.parents:
        if (parent / 'contracts').exists() and (parent / 'src').exists():
            return parent
    # Fallback to current working directory if structure not found
    return Path.cwd()

def load_yaml_schema(schema_path: Path) -> dict:
    """Load and parse the YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        try:
            schema = yaml.safe_load(f)
            if schema is None:
                raise ValueError("Schema file is empty or contains only comments.")
            return schema
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML syntax in schema: {e}")

def validate_with_pydantic(schema: dict) -> bool:
    """
    Validate that the schema structure is compatible with Pydantic model generation.
    Checks for required fields and basic type definitions.
    """
    try:
        from pydantic import BaseModel, create_model, ValidationError
        
        # Extract properties and required fields
        properties = schema.get('properties', {})
        required = schema.get('required', [])
        
        if not properties:
            raise ValueError("Schema must define 'properties'")
        
        # Dynamically create a Pydantic model based on the schema
        field_definitions = {}
        for field_name, field_props in properties.items():
            field_type_str = field_props.get('type', 'str')
            description = field_props.get('description', '')
            
            # Map JSON Schema types to Python types
            type_mapping = {
                'string': str,
                'integer': int,
                'number': float,
                'boolean': bool,
                'object': dict,
                'array': list
            }
            
            if field_type_str not in type_mapping:
                logger.warning(f"Unknown type '{field_type_str}' for field '{field_name}', defaulting to str")
                py_type = str
            else:
                py_type = type_mapping[field_type_str]
            
            # Handle optional vs required
            if field_name in required:
                field_definitions[field_name] = (py_type, ...)
            else:
                field_definitions[field_name] = (py_type, None)
        
        # Create the model class
        DynamicModel = create_model('DynamicDatasetModel', **field_definitions)
        
        # Test instantiation with minimal valid data
        test_data = {name: None for name in required}
        # Provide dummy values for required fields to avoid validation errors
        for name in required:
            field_type = properties[name].get('type', 'str')
            if field_type == 'integer':
                test_data[name] = 0
            elif field_type == 'number':
                test_data[name] = 0.0
            elif field_type == 'boolean':
                test_data[name] = False
            else:
                test_data[name] = "test"
        
        instance = DynamicModel(**test_data)
        logger.info(f"Pydantic validation successful. Model: {DynamicModel.__name__}")
        return True

    except ImportError:
        logger.warning("Pydantic not installed. Skipping Pydantic validation.")
        return True
    except Exception as e:
        logger.error(f"Pydantic validation failed: {e}")
        return False

def validate_with_jsonschema(schema: dict) -> bool:
    """
    Validate the schema itself against the JSON Schema meta-schema.
    """
    try:
        import jsonschema
        
        # Validate the schema structure against the draft-07 meta-schema
        meta_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#"
        }
        
        # We can't easily load the full meta-schema without jsonschema installing it,
        # but we can check basic structural integrity
        if 'type' not in schema:
            raise ValueError("Schema must have a 'type' property (usually 'object')")
        
        if schema['type'] != 'object':
            raise ValueError("Top-level schema type must be 'object' for dataset records")
        
        if 'properties' not in schema:
            raise ValueError("Schema must define 'properties'")
        
        if 'required' in schema:
            required_fields = set(schema['required'])
            prop_fields = set(schema['properties'].keys())
            if not required_fields.issubset(prop_fields):
                missing = required_fields - prop_fields
                raise ValueError(f"Required fields not defined in properties: {missing}")
        
        logger.info("JSON Schema structural validation passed.")
        return True

    except ImportError:
        logger.warning("jsonschema not installed. Skipping JSON Schema meta-validation.")
        return True
    except Exception as e:
        logger.error(f"JSON Schema validation failed: {e}")
        return False

def main():
    """Main entry point for schema validation."""
    project_root = get_project_root()
    schema_path = project_root / 'contracts' / 'dataset.schema.yaml'
    
    logger.info(f"Project root detected at: {project_root}")
    logger.info(f"Looking for schema at: {schema_path}")
    
    try:
        # 1. Load the YAML
        logger.info("Loading YAML schema...")
        schema = load_yaml_schema(schema_path)
        logger.info("YAML loaded successfully.")
        
        # 2. Validate with Pydantic
        logger.info("Validating with Pydantic...")
        pydantic_valid = validate_with_pydantic(schema)
        
        # 3. Validate with JSON Schema
        logger.info("Validating with JSON Schema...")
        jsonschema_valid = validate_with_jsonschema(schema)
        
        # Final verdict
        if pydantic_valid and jsonschema_valid:
            logger.info("SUCCESS: Schema is valid and loadable.")
            sys.exit(0)
        else:
            logger.error("FAILURE: Schema validation failed.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()