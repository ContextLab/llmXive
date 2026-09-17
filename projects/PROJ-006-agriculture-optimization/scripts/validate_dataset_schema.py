"""
Script to validate the dataset schema YAML against pydantic/jsonschema.
This serves as the verification script for T007.
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
    """Get the project root directory."""
    return Path(__file__).parent.parent

def load_yaml_schema(schema_path: Path) -> dict:
    """Load and parse the YAML schema file."""
    try:
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        if schema is None:
            raise ValueError("Schema file is empty or invalid YAML")
        return schema
    except FileNotFoundError:
        logger.error(f"Schema file not found: {schema_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"YAML parsing error: {e}")
        raise

def validate_with_pydantic(schema_dict: dict) -> bool:
    """
    Validate the schema structure using pydantic models.
    We define a simple model to ensure the schema has the expected structure.
    """
    try:
        from pydantic import BaseModel, Field, ValidationError
        
        class ColumnSpec(BaseModel):
            type: str
            description: str
        
        class DatasetSchema(BaseModel):
            columns: dict[str, ColumnSpec]
        
        # Validate the loaded schema structure
        validated = DatasetSchema(**schema_dict)
        logger.info(f"Pydantic validation successful. Found {len(validated.columns)} columns.")
        return True
    except ImportError:
        logger.warning("Pydantic not installed, skipping pydantic validation.")
        return True
    except ValidationError as e:
        logger.error(f"Pydantic validation failed: {e}")
        return False

def validate_with_jsonschema(schema_dict: dict) -> bool:
    """
    Validate the schema structure using jsonschema.
    """
    try:
        import jsonschema
        
        # Define a JSON Schema that matches our expected YAML structure
        json_schema = {
            "type": "object",
            "properties": {
                "columns": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string"},
                            "description": {"type": "string"}
                        },
                        "required": ["type", "description"]
                    }
                }
            },
            "required": ["columns"]
        }
        
        jsonschema.validate(instance=schema_dict, schema=json_schema)
        logger.info("JSON Schema validation successful.")
        return True
    except ImportError:
        logger.warning("jsonschema not installed, skipping jsonschema validation.")
        return True
    except jsonschema.ValidationError as e:
        logger.error(f"JSON Schema validation failed: {e}")
        return False

def main():
    """Main entry point for schema validation."""
    project_root = get_project_root()
    schema_path = project_root / "contracts" / "dataset.schema.yaml"
    
    logger.info(f"Validating schema at: {schema_path}")
    
    if not schema_path.exists():
        logger.error(f"Schema file does not exist: {schema_path}")
        sys.exit(1)
    
    try:
        schema_dict = load_yaml_schema(schema_path)
    except Exception:
        sys.exit(1)
    
    pydantic_ok = validate_with_pydantic(schema_dict)
    jsonschema_ok = validate_with_jsonschema(schema_dict)
    
    if pydantic_ok and jsonschema_ok:
        logger.info("All validations passed. Schema is valid.")
        sys.exit(0)
    else:
        logger.error("Schema validation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()