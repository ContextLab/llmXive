"""
Setup script to validate and write schema contracts.
This script ensures the schema files exist and are valid YAML.
"""
import os
import sys
from pathlib import Path
import yaml

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger

logger = get_logger(__name__)

def validate_yaml_schema(file_path: Path) -> bool:
    """Validate that a file contains valid YAML."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            yaml.safe_load(f)
        logger.info(f"Schema {file_path} is valid YAML.")
        return True
    except yaml.YAMLError as e:
        logger.error(f"Schema {file_path} is invalid YAML: {e}")
        return False
    except FileNotFoundError:
        logger.error(f"Schema file {file_path} not found.")
        return False

def main():
    """Ensure schema contracts are present."""
    contracts_dir = project_root / "contracts"
    contracts_dir.mkdir(exist_ok=True)

    ingest_schema_path = contracts_dir / "ingest.schema.yaml"
    dataset_schema_path = contracts_dir / "dataset.schema.yaml"

    logger.info("Checking schema contracts...")

    # Check Ingest Schema
    if not ingest_schema_path.exists():
        logger.warning(f"Missing {ingest_schema_path}. This task should create it.")
        # In a real implementation, this file would be created via artifact generation.
        # Since we are implementing T004, the file content is provided in the artifacts.
        # This script just validates existence if it were to be run later.
        return False
    
    # Check Dataset Schema
    if not dataset_schema_path.exists():
        logger.warning(f"Missing {dataset_schema_path}. This task should create it.")
        return False

    # Validate content
    valid = True
    if not validate_yaml_schema(ingest_schema_path):
        valid = False
    if not validate_yaml_schema(dataset_schema_path):
        valid = False

    if valid:
        logger.info("All schema contracts are valid.")
    else:
        logger.error("Schema validation failed.")
        return False

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
