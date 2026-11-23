"""
Validation script for the quickstart pipeline.
Verifies that all required JSON and CSV outputs exist and match expected schemas.
"""
import os
import json
import sys
import csv
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.logging_utils import get_logger
from config import get_output_dir

logger = get_logger(__name__)

# Define expected output files and their schemas
EXPECTED_FILES = {
    "data/results/final_report.json": {
        "required_keys": ["metadata", "correlation_results", "vif_results", "sensitivity_analysis", "non_linearity_test"],
        "metadata_required_keys": ["associational_framing", "random_seed", "timestamp"]
    },
    "data/results/sensitivity_pvalue.csv": {
        "required_columns": ["cutoff", "count_significant", "count_total", "random_seed"]
    },
    "data/results/sensitivity_rho.csv": {
        "required_columns": ["cutoff", "count_significant", "count_total", "random_seed"]
    }
}

def validate_json_structure(file_path: Path, schema: Dict[str, Any]) -> bool:
    """Validate a JSON file against a schema definition."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        # Check required top-level keys
        for key in schema.get("required_keys", []):
            if key not in data:
                logger.error(f"Missing required key '{key}' in {file_path}")
                return False

        # Check metadata required keys if specified
        if "metadata_required_keys" in schema and "metadata" in data:
            metadata = data["metadata"]
            for key in schema["metadata_required_keys"]:
                if key not in metadata:
                    logger.error(f"Missing required metadata key '{key}' in {file_path}")
                    return False

        # Special check for associational framing
        if "associational_framing" in data.get("metadata", {}):
            framing_text = data["metadata"]["associational_framing"]
            if "associational" not in framing_text.lower():
                logger.error(f"Associational framing text does not contain required keyword in {file_path}")
                return False

        logger.info(f"JSON validation passed for {file_path}")
        return True

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error validating JSON {file_path}: {e}")
        return False

def validate_csv_structure(file_path: Path, schema: Dict[str, Any]) -> bool:
    """Validate a CSV file against a schema definition."""
    try:
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

            if not headers:
                logger.error(f"Empty CSV file {file_path}")
                return False

            for col in schema.get("required_columns", []):
                if col not in headers:
                    logger.error(f"Missing required column '{col}' in {file_path}")
                    return False

            # Validate at least one row exists
            rows = list(reader)
            if len(rows) == 0:
                logger.error(f"CSV file {file_path} has no data rows")
                return False

            logger.info(f"CSV validation passed for {file_path} ({len(rows)} rows)")
            return True

    except Exception as e:
        logger.error(f"Error validating CSV {file_path}: {e}")
        return False

def validate_file_exists(file_path: Path) -> bool:
    """Check if a file exists."""
    if not file_path.exists():
        logger.error(f"Required file missing: {file_path}")
        return False
    logger.info(f"File exists: {file_path}")
    return True

def run_validation() -> bool:
    """Run all validations and return overall success status."""
    output_dir = Path(get_output_dir())
    all_passed = True

    logger.info("Starting quickstart validation...")

    for file_rel_path, schema in EXPECTED_FILES.items():
        file_path = output_dir.parent / file_rel_path

        # Check file exists
        if not validate_file_exists(file_path):
            all_passed = False
            continue

        # Validate structure based on file type
        if file_path.suffix == '.json':
            if not validate_json_structure(file_path, schema):
                all_passed = False
        elif file_path.suffix == '.csv':
            if not validate_csv_structure(file_path, schema):
                all_passed = False

    if all_passed:
        logger.info("✓ All validations passed!")
    else:
        logger.error("✗ Some validations failed.")

    return all_passed

def main():
    """Main entry point."""
    success = run_validation()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
