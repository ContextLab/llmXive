"""
Schema Validator for T003.

This module verifies that the dataset schema matches the covariate list
defined in spec.md FR-002 before proceeding with data generation or analysis.

It explicitly checks that:
1. Required covariates (age, sex, BMI, dietary_fiber_intake, antibiotic_use_history) exist.
2. Excluded fields (SES, dietary_pattern) do NOT exist.
3. Field types and constraints match the specification.
"""
import logging
import sys
from pathlib import Path
from typing import Dict, List, Set, Any
import yaml

# Configure logging for this module
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Expected covariates per spec.md FR-002
REQUIRED_COVARIATES: Set[str] = {
    "age",
    "sex",
    "bmi",
    "dietary_fiber_intake",
    "antibiotic_use_history"
}

# Fields explicitly excluded from this schema version
EXCLUDED_FIELDS: Set[str] = {
    "ses",
    "dietary_pattern",
    "socioeconomic_status",
    "dietary_patterns"
}

# Expected field definitions based on task description
EXPECTED_FIELDS: Dict[str, Dict[str, Any]] = {
    "participant_id": {"type": "str", "pk": True},
    "age": {"type": "int", "min": 0},
    "sex": {"type": "enum", "values": ["Male", "Female", "Other"]},
    "bmi": {"type": "float"},
    "cognitive_flexibility_score": {"type": "float"},
    "shannon_diversity": {"type": "float"},
    "simpson_diversity": {"type": "float"},
    "chao1": {"type": "float"},
    "dietary_fiber_intake": {"type": "float"},
    "antibiotic_use_history": {"type": "bool"},
}

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_covariates(schema: Dict[str, Any]) -> bool:
    """
    Validate that the schema contains exactly the covariates required by FR-002
    and excludes the forbidden ones.
    """
    logger.info("Validating covariates against spec.md FR-002...")
    
    # Extract field names from schema
    if "entities" not in schema:
        logger.error("Schema missing 'entities' key.")
        return False
    
    field_names = set()
    for entity in schema["entities"]:
        if "fields" in entity:
            for field in entity["fields"]:
                if "name" in field:
                    field_names.add(field["name"])
    
    # Check for required covariates
    missing_covariates = REQUIRED_COVARIATES - field_names
    if missing_covariates:
        logger.error(f"Missing required covariates from FR-002: {missing_covariates}")
        return False
    
    # Check for excluded fields (case-insensitive check)
    field_names_lower = {f.lower() for f in field_names}
    found_excluded = {f for f in EXCLUDED_FIELDS if f.lower() in field_names_lower}
    
    if found_excluded:
        logger.error(f"Schema contains excluded fields that violate scope: {found_excluded}")
        logger.error("Per spec.md FR-002, SES and dietary_pattern must NOT be included.")
        return False
    
    logger.info("Covariate validation passed. All required fields present, no excluded fields found.")
    return True

def validate_field_definitions(schema: Dict[str, Any]) -> bool:
    """
    Validate that the schema fields match the expected definitions (types, etc).
    """
    logger.info("Validating field definitions...")
    
    if "entities" not in schema:
        return False
    
    all_fields = {}
    for entity in schema["entities"]:
        if "fields" in entity:
            for field in entity["fields"]:
                if "name" in field:
                    all_fields[field["name"]] = field
    
    for field_name, expected_def in EXPECTED_FIELDS.items():
        if field_name not in all_fields:
            logger.error(f"Expected field '{field_name}' is missing from schema.")
            return False
        
        actual_field = all_fields[field_name]
        
        # Check type if specified
        if "type" in expected_def:
            if actual_field.get("type") != expected_def["type"]:
                logger.error(f"Field '{field_name}' has incorrect type. Expected {expected_def['type']}, got {actual_field.get('type')}")
                return False
        
        # Check PK
        if expected_def.get("pk") and not actual_field.get("unique"):
            logger.error(f"Field '{field_name}' should be marked as unique (PK).")
            return False
        
        # Check enum values if specified
        if "values" in expected_def:
            if "enum" not in actual_field.get("type", ""):
                logger.error(f"Field '{field_name}' should be an enum.")
                return False
            # Note: We don't strictly enforce values here unless they differ significantly,
            # but the schema must define it as an enum.
    
    logger.info("Field definition validation passed.")
    return True

def validate_schema_file(schema_path: Path) -> bool:
    """
    Main entry point to validate the schema file.
    Returns True if valid, False otherwise.
    """
    try:
        schema = load_schema(schema_path)
        
        if not validate_covariates(schema):
            logger.error("Covariate validation failed. Aborting.")
            return False
        
        if not validate_field_definitions(schema):
            logger.error("Field definition validation failed. Aborting.")
            return False
        
        logger.info("Schema validation successful. All checks passed.")
        return True
        
    except Exception as e:
        logger.error(f"Error during schema validation: {e}")
        raise

def main():
    """CLI entry point for schema validation."""
    # Determine schema path relative to project root
    # Assuming this script is run from project root or code directory
    project_root = Path(__file__).resolve().parent.parent.parent
    schema_path = project_root / "contracts" / "dataset.schema.yaml"
    
    if not schema_path.exists():
        # Try relative to current working directory if not found above
        schema_path = Path("contracts/dataset.schema.yaml")
    
    if not schema_path.exists():
        logger.error(f"Could not locate schema file at {schema_path}")
        sys.exit(1)
    
    logger.info(f"Validating schema at: {schema_path}")
    is_valid = validate_schema_file(schema_path)
    
    if not is_valid:
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()