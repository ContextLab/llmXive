"""
Validation script for ROI timecourses CSV against neural-data schema.
Implements T021: Run validation script against data/processed/roi_timecourses.csv
"""
import os
import sys
import json
import csv
import yaml
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.schema_validation import validate_neural_data
from utils.logging_config import get_logger, info, error, warning
from config import get_config


def load_schema(schema_path: str) -> dict:
    """Load YAML schema file."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)


def validate_csv_against_schema(csv_path: str, schema_path: str) -> bool:
    """
    Validate a CSV file against a YAML schema.
    Uses the validate_neural_data function from schema_validation module.
    
    Args:
        csv_path: Path to the CSV file to validate
        schema_path: Path to the YAML schema file
        
    Returns:
        bool: True if validation passes, False otherwise
    """
    logger = get_logger()
    logger.info(f"Validating {csv_path} against {schema_path}")
    
    if not os.path.exists(csv_path):
        error(f"File not found: {csv_path}")
        return False
    
    if not os.path.exists(schema_path):
        error(f"Schema file not found: {schema_path}")
        return False
    
    try:
        # Use the existing validate_neural_data function
        is_valid = validate_neural_data(csv_path, schema_path)
        
        if is_valid:
            info("Validation PASSED: CSV conforms to schema")
        else:
            error("Validation FAILED: CSV does not conform to schema")
            
        return is_valid
        
    except Exception as e:
        error(f"Validation error: {str(e)}")
        return False


def main():
    """Main entry point for validation script."""
    config = get_config()
    logger = get_logger()
    
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    csv_path = project_root / "data" / "processed" / "roi_timecourses.csv"
    schema_path = project_root / "specs" / "001-neural-narrative-networks-brain-inspired" / "contracts" / "neural-data.schema.yaml"
    
    logger.info("Starting ROI timecourses validation (T021)")
    logger.info(f"CSV file: {csv_path}")
    logger.info(f"Schema file: {schema_path}")
    
    # Validate
    is_valid = validate_csv_against_schema(str(csv_path), str(schema_path))
    
    # Exit with appropriate code
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()