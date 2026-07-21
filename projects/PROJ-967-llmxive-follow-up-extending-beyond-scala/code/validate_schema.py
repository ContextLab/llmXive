import argparse
import csv
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any

import yaml

from code.download_zreward import calculate_sha256

def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """Configure logging for the validation script."""
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger(__name__)

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load and parse the YAML schema contract."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    
    if not isinstance(schema, dict):
        raise ValueError("Schema file must contain a YAML dictionary")
    
    return schema

def get_expected_columns(schema: Dict[str, Any]) -> List[str]:
    """Extract required column names from the schema definition."""
    required_fields = schema.get("required_fields", [])
    if not required_fields:
        raise ValueError("Schema missing 'required_fields' key")
    
    # Ensure we have a flat list of strings
    columns = []
    for field in required_fields:
        if isinstance(field, dict):
            # Handle nested schema definitions if present
            columns.extend(field.get("columns", []))
        elif isinstance(field, str):
            columns.append(field)
        else:
            raise ValueError(f"Invalid field format in schema: {field}")
    
    return columns

def validate_dataset(
    dataset_path: Path, 
    expected_columns: List[str],
    logger: logging.Logger
) -> bool:
    """
    Validate that the dataset CSV contains all required columns.
    
    Args:
        dataset_path: Path to the CSV dataset file
        expected_columns: List of required column names
        logger: Logger instance for output
    
    Returns:
        True if validation passes, False otherwise
    
    Raises:
        FileNotFoundError: If dataset file doesn't exist
        ValueError: If schema validation fails
    """
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")
    
    logger.info(f"Validating dataset: {dataset_path}")
    logger.info(f"Expected columns: {expected_columns}")
    
    with open(dataset_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        
        # Normalize headers (strip whitespace)
        header = [col.strip() for col in header]
        
        logger.info(f"Dataset columns: {header}")
        
        # Check for missing columns
        missing_columns = []
        for col in expected_columns:
            if col not in header:
                missing_columns.append(col)
        
        if missing_columns:
            error_msg = (
                f"Schema validation FAILED. Missing required columns: {missing_columns}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Validate row count (at least one data row)
        row_count = sum(1 for _ in reader)
        logger.info(f"Dataset contains {row_count} data rows")
        
        if row_count == 0:
            logger.warning("Dataset is empty (no data rows)")
        
        logger.info("Schema validation PASSED")
        return True

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Validate dataset schema against contract"
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("contracts/dataset.schema.yaml"),
        help="Path to the schema contract file"
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("data/raw/zreward_dataset.csv"),
        help="Path to the dataset CSV file"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    return parser.parse_args()

def main() -> int:
    """Main entry point for schema validation."""
    args = parse_args()
    logger = setup_logging(getattr(logging, args.log_level))
    
    try:
        # Load schema
        schema = load_schema(args.schema)
        logger.info(f"Loaded schema from {args.schema}")
        
        # Get expected columns
        expected_columns = get_expected_columns(schema)
        
        # Validate dataset
        validate_dataset(args.dataset, expected_columns, logger)
        
        logger.info("All validations passed successfully")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation failed: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during validation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
