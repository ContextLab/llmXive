"""
Manifest Schema Validator module.
Validates output/manifest.json against contracts/manifest.schema.yaml.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from code.src.contracts.validation import SchemaValidator, get_default_logger

MANIFEST_PATH = Path("output/manifest.json")
SCHEMA_PATH = Path("contracts/manifest.schema.yaml")

def load_manifest(path: Path = MANIFEST_PATH) -> Optional[Dict[str, Any]]:
    """Load the manifest JSON file."""
    if not path.exists():
        logger = get_default_logger()
        logger.error(f"Manifest file not found at {path}")
        return None
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        logger = get_default_logger()
        logger.error(f"Failed to parse manifest JSON: {e}")
        return None

def validate_manifest_schema(
    manifest_data: Dict[str, Any],
    schema_path: Path = SCHEMA_PATH
) -> Tuple[bool, List[str]]:
    """
    Validate manifest data against the schema.
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    validator = SchemaValidator(schema_path)
    is_valid, errors = validator.validate(manifest_data)
    return is_valid, errors

def run_manifest_schema_validation(
    manifest_path: Path = MANIFEST_PATH,
    schema_path: Path = SCHEMA_PATH
) -> bool:
    """
    Run the full validation pipeline: load manifest, validate against schema.
    
    Returns:
        True if validation passes, False otherwise.
    """
    logger = get_default_logger()
    
    # Load manifest
    logger.info(f"Loading manifest from {manifest_path}")
    manifest_data = load_manifest(manifest_path)
    
    if manifest_data is None:
        logger.error("Manifest loading failed. Aborting validation.")
        return False
    
    # Validate schema
    logger.info(f"Validating manifest against schema at {schema_path}")
    is_valid, errors = validate_manifest_schema(manifest_data, schema_path)
    
    if not is_valid:
        logger.error("Manifest schema validation FAILED:")
        for error in errors:
            logger.error(f"  - {error}")
        return False
    
    logger.info("Manifest schema validation PASSED.")
    return True

def main() -> int:
    """Entry point for CLI execution."""
    logger = get_default_logger()
    logger.info("Starting manifest schema validation (Task T058)...")
    
    success = run_manifest_schema_validation()
    
    if success:
        logger.info("Task T058 completed successfully.")
        return 0
    else:
        logger.error("Task T058 failed: Manifest validation errors detected.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
