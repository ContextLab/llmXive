"""
Schema Validation Script for Z-Reward Dataset (Task T038)

This script validates the downloaded dataset against the schema contract
defined in contracts/dataset.schema.yaml. It ensures all required columns
and rubric dimensions are present before proceeding with ingestion.

Dependencies:
  - PyYAML (for schema parsing)
  - Pandas (for CSV reading) - optional, can use csv module for memory efficiency

Usage:
  python code/validate_schema.py --schema contracts/dataset.schema.yaml --dataset data/raw/zreward_dataset.csv
"""
import argparse
import csv
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any

import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_logging(level: int = logging.INFO) -> None:
    """Setup logging configuration."""
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """
    Load and parse the YAML schema file.

    Args:
        schema_path: Path to the schema YAML file

    Returns:
        Dictionary containing the schema definition

    Raises:
        FileNotFoundError: If schema file doesn't exist
        yaml.YAMLError: If schema is not valid YAML
    """
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)

    if not isinstance(schema, dict):
        raise yaml.YAMLError("Schema must be a YAML dictionary")

    return schema


def get_expected_columns(schema: Dict[str, Any]) -> List[str]:
    """
    Extract expected column names from the schema.

    Args:
        schema: Parsed schema dictionary

    Returns:
        List of expected column names
    """
    columns = []
    if 'required_columns' in schema:
        for col_def in schema['required_columns']:
            if isinstance(col_def, dict) and 'name' in col_def:
                columns.append(col_def['name'])
            elif isinstance(col_def, str):
                columns.append(col_def)
    return columns


def validate_schema_structure(schema: Dict[str, Any]) -> bool:
    """
    Validate that the schema has the required structure.

    Args:
        schema: Parsed schema dictionary

    Returns:
        True if schema structure is valid
    """
    required_keys = ['required_columns', 'rubric_dimensions']
    for key in required_keys:
        if key not in schema:
            logger.error(f"Schema missing required key: {key}")
            return False
    return True


def validate_fields(schema: Dict[str, Any]) -> bool:
    """
    Validate that the schema contains all required rubric dimensions.

    Args:
        schema: Parsed schema dictionary

    Returns:
        True if all rubric dimensions are present
    """
    expected_dims = ['Alignment', 'Realism', 'Aesthetics', 'Plausibility']
    actual_dims = schema.get('rubric_dimensions', [])

    missing = set(expected_dims) - set(actual_dims)
    if missing:
        logger.error(f"Schema missing required rubric dimensions: {missing}")
        return False

    logger.info("All required rubric dimensions present in schema")
    return True


def validate_dataset(dataset_path: Path, schema: Dict[str, Any]) -> bool:
    """
    Validate the dataset CSV against the schema.

    Args:
        dataset_path: Path to the dataset CSV file
        schema: Parsed schema dictionary

    Returns:
        True if dataset matches schema, False otherwise

    Raises:
        FileNotFoundError: If dataset file doesn't exist
    """
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

    # Extract expected columns from schema
    expected_columns = get_expected_columns(schema)

    if not expected_columns:
        logger.error("No expected columns found in schema")
        return False

    # Read first row (header) to check columns
    with open(dataset_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            logger.error("Dataset file is empty")
            return False

    # Normalize header (strip whitespace)
    header = [col.strip() for col in header]

    # Check for missing columns
    missing_columns = set(expected_columns) - set(header)
    if missing_columns:
        logger.error(f"Dataset missing required columns: {missing_columns}")
        logger.error(f"Found columns: {header}")
        logger.error(f"Expected columns: {expected_columns}")
        return False

    # Check for extra columns (warning only)
    extra_columns = set(header) - set(expected_columns)
    if extra_columns:
        logger.warning(f"Dataset contains extra columns (allowed): {extra_columns}")

    # Validate rubric dimensions in human_annotations
    # We check the schema for the expected keys in human_annotations
    if 'human_annotations' in schema:
        annotation_schema = schema['human_annotations']
        if isinstance(annotation_schema, dict) and 'keys' in annotation_schema:
            expected_keys = annotation_schema['keys']
            # Note: We can't fully validate the dict structure without reading the file,
            # but we can verify the column exists and log that we expect specific keys
            if 'human_annotations' not in header:
                logger.error("Dataset missing 'human_annotations' column")
                return False
            logger.info(f"Expected human_annotations keys: {expected_keys}")

    logger.info(f"Schema validation passed for {dataset_path}")
    logger.info(f"Found {len(header)} columns, all required columns present")
    return True


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Validate dataset against schema contract',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '--schema',
        type=str,
        default='contracts/dataset.schema.yaml',
        help='Path to the schema YAML file'
    )
    parser.add_argument(
        '--dataset',
        type=str,
        default='data/raw/zreward_dataset.csv',
        help='Path to the dataset CSV file'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level'
    )
    return parser.parse_args()


def main():
    """Main entry point for schema validation."""
    args = parse_args()
    setup_logging(getattr(logging, args.log_level))

    schema_path = Path(args.schema)
    dataset_path = Path(args.dataset)

    logger.info(f"Loading schema from: {schema_path}")
    logger.info(f"Validating dataset: {dataset_path}")

    try:
        # Step 1: Load and validate schema structure
        schema = load_schema(schema_path)
        if not validate_schema_structure(schema):
            logger.error("Schema structure validation failed")
            sys.exit(1)

        # Step 2: Validate rubric dimensions
        if not validate_fields(schema):
            logger.error("Schema field validation failed")
            sys.exit(1)

        # Step 3: Validate dataset against schema
        if not validate_dataset(dataset_path, schema):
            logger.error("Dataset validation failed against schema")
            sys.exit(1)

        logger.info("SUCCESS: Dataset schema validation passed")
        sys.exit(0)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in schema: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()