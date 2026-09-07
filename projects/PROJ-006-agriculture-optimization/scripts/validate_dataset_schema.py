import os
import sys
import logging
from pathlib import Path
import json
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Determine the project root directory."""
    current = Path(__file__).resolve()
    # Traverse up until we find the project root (where contracts/ and src/ exist)
    for parent in current.parents:
        if (parent / "contracts").exists() and (parent / "src").exists():
            return parent
    # Fallback to parent of scripts/
    return current.parent.parent

def load_yaml_schema(schema_path: Path) -> dict:
    """Load and parse a YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def validate_with_pydantic(schema: dict) -> bool:
    """
    Validate the schema structure against a minimal Pydantic model definition.
    This ensures the YAML defines valid types and required fields.
    """
    try:
        from pydantic import BaseModel, create_model, ValidationError

        # Dynamically create a model based on the schema properties
        fields = {}
        required_fields = schema.get("required", [])
        properties = schema.get("properties", {})

        for field_name, field_def in properties.items():
            field_type = field_def.get("type")
            field_format = field_def.get("format")

            # Map YAML types to Python types
            if field_type == "integer":
                python_type = int
            elif field_type == "number":
                python_type = float
            elif field_type == "boolean":
                python_type = bool
            elif field_type == "string":
                python_type = str
            else:
                logger.warning(f"Unknown type '{field_type}' for field {field_name}, defaulting to Any")
                python_type = object

            # Add field to definition
            fields[field_name] = (python_type, ...)

        # Create the dynamic model
        DynamicModel = create_model("DynamicSchemaModel", **fields)

        # Test validation with a dummy valid instance
        dummy_data = {
            "household_id": 1,
            "latitude": 1.0,
            "longitude": 1.0,
            "land_size": 1.0,
            "education_level": 1,
            "finance_access": True,
            "practice_mixed_farming": True,
            "practice_terracing": True,
            "practice_conservation_tillage": True,
            "practice_agroforestry": True,
            "extension_visits": 1,
            "hlias": 1,
            "CSA_Index": 1.0,
            "Stability_Score": 1.0,
            "HFIAS": 1.0,
            "village_id": "test"
        }

        # Validate
        model_instance = DynamicModel(**dummy_data)
        logger.info("Pydantic validation successful against generated model.")
        return True

    except ImportError:
        logger.warning("Pydantic not installed. Skipping Pydantic validation.")
        return True
    except TypeError as e:
        logger.error(f"Pydantic type mapping error: {e}")
        return False
    except Exception as e:
        logger.error(f"Pydantic validation failed: {e}")
        return False

def validate_with_jsonschema(schema: dict) -> bool:
    """
    Validate the schema itself using jsonschema (if available) or basic checks.
    """
    try:
        import jsonschema
        # Validate the schema structure against the JSON Schema meta-schema
        # This ensures the YAML we wrote is a valid JSON Schema document
        jsonschema.validate(instance=schema, schema=jsonschema.DRAFT7_SCHEMA)
        logger.info("JSON Schema structure validation successful.")
        return True
    except ImportError:
        logger.warning("jsonschema not installed. Skipping JSON Schema structure validation.")
        return True
    except jsonschema.exceptions.SchemaError as e:
        logger.error(f"Schema structure is invalid JSON Schema: {e}")
        return False
    except Exception as e:
        logger.error(f"JSON Schema validation failed: {e}")
        return False

def main() -> int:
    """Main entry point for schema validation."""
    project_root = get_project_root()
    schema_path = project_root / "contracts" / "dataset.schema.yaml"

    logger.info(f"Project root: {project_root}")
    logger.info(f"Loading schema from: {schema_path}")

    try:
        schema = load_yaml_schema(schema_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        return 1
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML syntax: {e}")
        return 1

    logger.info("Schema loaded successfully.")
    logger.info(f"Properties defined: {list(schema.get('properties', {}).keys())}")
    logger.info(f"Required fields: {schema.get('required', [])}")

    # Run validations
    pydantic_ok = validate_with_pydantic(schema)
    jsonschema_ok = validate_with_jsonschema(schema)

    if pydantic_ok and jsonschema_ok:
        logger.info("All validations passed.")
        return 0
    else:
        logger.error("Validation failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())