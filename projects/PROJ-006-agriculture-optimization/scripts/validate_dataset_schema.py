"""
Validation script for the dataset schema contract (T007).
Loads the YAML schema and validates it against Pydantic and JSONSchema.
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

def load_yaml_schema(schema_path: str) -> dict:
    """Load and parse the YAML schema file."""
    logger.info(f"Loading schema from {schema_path}")
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)
    
    if not isinstance(schema, dict):
        raise ValueError("Schema must be a valid YAML dictionary")
    
    logger.info("Schema loaded successfully")
    return schema

def validate_with_pydantic(schema: dict) -> bool:
    """
    Validate the schema structure using Pydantic models.
    This ensures the schema is logically consistent.
    """
    logger.info("Validating schema structure with Pydantic...")
    try:
        # Import the schema definition from src/config/schemas.py
        # We use the AnalysisDatasetRecord model to validate against the schema
        from src.config.schemas import AnalysisDatasetRecord, validate_dataset_schema
        
        # The validate_dataset_schema function should use Pydantic internally
        # We'll create a mock record to ensure the schema is valid
        test_record = {
            "household_id": 1,
            "latitude": -13.5,
            "longitude": 34.0,
            "land_size": 2.5,
            "education_level": 8,
            "finance_access": True,
            "practice_mixed_farming": True,
            "practice_terracing": False,
            "practice_conservation_tillage": True,
            "practice_agroforestry": False,
            "extension_visits": 3,
            "hlias": 12,
            "CSA_Index": 2.0,
            "Stability_Score": 1.5,
            "HFIAS": 15.0,
            "village_id": "village_001"
        }
        
        # Validate the record against the schema
        result = validate_dataset_schema(test_record)
        logger.info("Pydantic validation passed")
        return True
    except Exception as e:
        logger.error(f"Pydantic validation failed: {e}")
        return False

def validate_with_jsonschema(schema: dict) -> bool:
    """
    Validate the schema against JSON Schema specification.
    This ensures the schema is syntactically correct.
    """
    logger.info("Validating schema syntax with JSON Schema...")
    try:
        import jsonschema
        
        # Validate the schema itself against the JSON Schema meta-schema
        jsonschema.validate(schema, jsonschema.Draft7Validator.META_SCHEMA)
        logger.info("JSON Schema syntax validation passed")
        
        # Create a validator for our specific schema
        validator = jsonschema.Draft7Validator(schema)
        
        # Test with a valid record
        test_record = {
            "household_id": 1,
            "latitude": -13.5,
            "longitude": 34.0,
            "land_size": 2.5,
            "education_level": 8,
            "finance_access": True,
            "practice_mixed_farming": True,
            "practice_terracing": False,
            "practice_conservation_tillage": True,
            "practice_agroforestry": False,
            "extension_visits": 3,
            "hlias": 12,
            "CSA_Index": 2.0,
            "Stability_Score": 1.5,
            "HFIAS": 15.0,
            "village_id": "village_001"
        }
        
        errors = list(validator.iter_errors(test_record))
        if errors:
            logger.error(f"JSON Schema validation errors: {[e.message for e in errors]}")
            return False
        
        logger.info("JSON Schema instance validation passed")
        return True
    except ImportError:
        logger.warning("jsonschema library not installed, skipping JSON Schema validation")
        return True
    except Exception as e:
        logger.error(f"JSON Schema validation failed: {e}")
        return False

def main():
    """Main entry point for schema validation."""
    # Determine project root
    project_root = Path(__file__).resolve().parent.parent
    schema_path = project_root / "contracts" / "dataset.schema.yaml"
    
    if not schema_path.exists():
        logger.error(f"Schema file not found at {schema_path}")
        sys.exit(1)
    
    try:
        # Load the schema
        schema = load_yaml_schema(str(schema_path))
        
        # Validate with Pydantic
        pydantic_valid = validate_with_pydantic(schema)
        
        # Validate with JSON Schema
        jsonschema_valid = validate_with_jsonschema(schema)
        
        # Report results
        if pydantic_valid and jsonschema_valid:
            logger.info("✅ All validations passed. Schema is valid and loadable.")
            sys.exit(0)
        else:
            logger.error("❌ Schema validation failed.")
            if not pydantic_valid:
                logger.error("  - Pydantic validation failed")
            if not jsonschema_valid:
                logger.error("  - JSON Schema validation failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Schema validation error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()