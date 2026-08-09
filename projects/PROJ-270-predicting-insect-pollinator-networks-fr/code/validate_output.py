"""
Validation script to ensure the preprocessing output matches the dataset schema.
This script loads the processed feature matrix and validates it against
code/contracts/dataset.schema.yaml using the jsonschema library.
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict

import yaml
from jsonschema import validate, ValidationError, Draft7Validator

# Import project utilities
from config import get_data_processed, get_project_root
from utils.logger import get_logger

# Setup logger
logger = get_logger(__name__)

SCHEMA_PATH = "code/contracts/dataset.schema.yaml"
# Expected output file from preprocessing (T019)
OUTPUT_FILE_NAME = "feature_matrix.json"

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load and parse the YAML schema file."""
    full_path = get_project_root() / schema_path
    if not full_path.exists():
        raise FileNotFoundError(f"Schema file not found at {full_path}")
    
    with open(full_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def load_output_data(output_path: Path) -> Dict[str, Any]:
    """Load the processed dataset JSON."""
    if not output_path.exists():
        raise FileNotFoundError(f"Output file not found at {output_path}")
    
    with open(output_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_structure(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate the data against the schema using jsonschema.
    Returns True if valid, raises ValidationError otherwise.
    """
    # Use Draft7Validator for better error messages if needed, 
    # but validate() is sufficient for boolean check + exception raising.
    try:
        validate(instance=data, schema=schema)
        return True
    except ValidationError as e:
        logger.error(f"Schema validation failed: {e.message}")
        logger.error(f"Path: {list(e.path)}")
        logger.error(f"Instance value: {e.instance}")
        raise

def main() -> int:
    """
    Main entry point for validation.
    Returns 0 if valid, 1 if invalid or error occurs.
    """
    try:
        # 1. Resolve paths
        output_file = get_data_processed() / OUTPUT_FILE_NAME
        logger.info(f"Validating output: {output_file}")
        
        # 2. Load Schema
        schema = load_schema(SCHEMA_PATH)
        logger.info(f"Schema loaded from {SCHEMA_PATH}")

        # 3. Load Data
        data = load_output_data(output_file)
        logger.info(f"Data loaded from {output_file}")

        # 4. Validate
        # The schema defines required fields in metadata and structure in data items.
        # We rely on jsonschema for strict validation.
        if validate_structure(data, schema):
            logger.info("✅ Validation PASSED: Output matches dataset schema.")
            
            # Log summary stats for transparency
            metadata = data.get('metadata', {})
            logger.info(f"   - Ecosystems: {metadata.get('source_ecosystems', [])}")
            logger.info(f"   - Total Pairs: {metadata.get('total_pairs', 0)}")
            logger.info(f"   - Positive: {metadata.get('positive_pairs', 0)}")
            logger.info(f"   - Negative: {metadata.get('negative_pairs', 0)}")
            logger.info(f"   - Features: {len(metadata.get('feature_columns', []))}")
            
            return 0
        
    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        return 1
    except ValidationError as e:
        logger.error(f"Schema validation error: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
