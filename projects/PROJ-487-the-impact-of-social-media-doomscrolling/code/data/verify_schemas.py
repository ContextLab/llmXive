"""
Schema Verification Script (T008c)

This script verifies that the schema files defined in `contracts/` are:
1. Valid YAML files that can be parsed.
2. Loadable and usable by the `validation.py` utility.

It serves as the implementation for Task T008c.
"""
import os
import sys
import logging
import yaml
from pathlib import Path

# Add project root to path if necessary
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging import get_logger
from utils.validation import load_schema, ValidationError

logger = get_logger(__name__)

def verify_schema_file(schema_path: Path) -> bool:
    """
    Verifies that a schema file is valid YAML and loadable.
    
    Args:
        schema_path: Path to the schema file.
        
    Returns:
        True if valid, False otherwise.
    """
    logger.info(f"Verifying schema file: {schema_path}")
    
    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        return False

    try:
        # Attempt to load as YAML
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        
        if schema is None:
            logger.error(f"Schema file is empty or contains only null: {schema_path}")
            return False

        # Attempt to load using the project's validation utility
        loaded_schema = load_schema(str(schema_path))
        
        if loaded_schema is None:
            logger.error(f"Failed to load schema via validation utility: {schema_path}")
            return False

        logger.info(f"Schema loaded successfully: {schema_path}")
        logger.info(f"  - Title: {loaded_schema.get('title', 'N/A')}")
        logger.info(f"  - Properties count: {len(loaded_schema.get('properties', {}))}")
        
        return True

    except yaml.YAMLError as e:
        logger.error(f"YAML parsing error in {schema_path}: {e}")
        return False
    except ValidationError as e:
        logger.error(f"Validation error for {schema_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error loading {schema_path}: {e}")
        return False

def main():
    """
    Main entry point for schema verification.
    """
    logger.info("Starting schema verification (Task T008c)...")
    
    contracts_dir = project_root / "contracts"
    
    if not contracts_dir.exists():
        logger.error(f"Contracts directory not found: {contracts_dir}")
        sys.exit(1)

    schemas_to_verify = [
        contracts_dir / "dataset.schema.yaml",
        contracts_dir / "output.schema.yaml"
    ]

    all_passed = True
    for schema_path in schemas_to_verify:
        if not verify_schema_file(schema_path):
            all_passed = False

    if all_passed:
        logger.info("All schema verifications passed.")
        sys.exit(0)
    else:
        logger.error("Schema verification failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()