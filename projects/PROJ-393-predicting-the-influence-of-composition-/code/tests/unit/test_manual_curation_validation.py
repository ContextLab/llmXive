"""
Unit tests for Manual Curation Validation (T063).

This script validates the format and schema compliance of `data/raw/manual_curated.csv`
before it is ingested by the pipeline (T018). It serves as a pre-ingestion check
to ensure researchers have correctly followed the Manual Curation Guide.

Usage:
    python code/tests/unit/test_manual_curation_validation.py

If the file `data/raw/manual_curated.csv` does not exist, the test assumes
the manual path is not currently in use and passes (graceful degradation).
"""

import csv
import json
import sys
import os
from pathlib import Path
import re

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.schema_validator import load_schema, validate_csv_file
from src.utils.logging_config import setup_logging, create_logger

logger = create_logger("manual_curation_validation")

# Path constants
DATA_DIR = project_root / "data" / "raw"
MANUAL_CSV_PATH = DATA_DIR / "manual_curated.csv"
SCHEMA_PATH = project_root / "specs" / "001-predict-heusler-hysteresis" / "contracts" / "alloy_entry.schema.yaml"

# Required columns based on T057 template and T010 schema
REQUIRED_COLUMNS = [
    "composition",
    "coercivity_oe",
    "saturation_magnetization_emu_g",
    "source_type",
    "synthesis_method"
]

# Optional columns
OPTIONAL_COLUMNS = [
    "doi",
    "crystal_structure"
]

VALID_SOURCE_TYPES = ["Manual"] # Enforce strict source type for manual entries

def validate_composition_format(composition: str) -> bool:
    """
    Validates that the composition string follows standard chemical formula rules.
    Allows element symbols (e.g., Co, Mn, Ga) and integers (e.g., Co2MnGa).
    Does not allow spaces or invalid characters.
    """
    if not composition or not isinstance(composition, str):
        return False
    # Regex for chemical formulas: Element symbol followed optionally by a number
    # Element symbols are 1 or 2 letters, first uppercase, second lowercase
    pattern = r'^([A-Z][a-z]?[0-9]*)+$'
    return bool(re.match(pattern, composition))

def validate_numeric_field(value: str, field_name: str) -> bool:
    """
    Validates that a field can be converted to a float.
    Empty strings are allowed (handled by imputation later).
    """
    if value is None or value.strip() == "":
        return True # Missing values are allowed, will be imputed
    try:
        float(value)
        return True
    except ValueError:
        logger.error(f"Invalid numeric value for {field_name}: {value}")
        return False

def validate_manual_csv():
    """
    Main validation logic for manual_curated.csv.
    Returns True if validation passes, False otherwise.
    """
    # Check if file exists
    if not MANUAL_CSV_PATH.exists():
        logger.info(f"File {MANUAL_CSV_PATH} not found. Skipping validation (graceful degradation).")
        return True

    errors = []
    warnings = []

    try:
        with open(MANUAL_CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # 1. Validate Header
            if reader.fieldnames is None:
                errors.append("CSV file is empty or has no header.")
                return False

            header_set = set(reader.fieldnames)
            required_set = set(REQUIRED_COLUMNS)

            missing_required = required_set - header_set
            if missing_required:
                errors.append(f"Missing required columns: {missing_required}")

            # 2. Validate Rows
            row_count = 0
            for row_num, row in enumerate(reader, start=2): # Start at 2 (1 is header)
                row_count += 1

                # Check composition format
                comp = row.get("composition", "")
                if not validate_composition_format(comp):
                    errors.append(f"Row {row_num}: Invalid composition format '{comp}'. Expected format like 'Co2MnGa'.")

                # Check numeric fields
                if not validate_numeric_field(row.get("coercivity_oe", ""), "coercivity_oe"):
                    errors.append(f"Row {row_num}: Invalid coercivity_oe value '{row.get('coercivity_oe')}'.")

                if not validate_numeric_field(row.get("saturation_magnetization_emu_g", ""), "saturation_magnetization_emu_g"):
                    errors.append(f"Row {row_num}: Invalid saturation_magnetization_emu_g value '{row.get('saturation_magnetization_emu_g')}'.")

                # Check source_type
                source_type = row.get("source_type", "")
                if source_type not in VALID_SOURCE_TYPES:
                    errors.append(f"Row {row_num}: Invalid source_type '{source_type}'. Must be 'Manual'.")

                # Check synthesis_method (basic non-empty check)
                synthesis = row.get("synthesis_method", "")
                if not synthesis or synthesis.strip() == "":
                    warnings.append(f"Row {row_num}: Missing synthesis_method. This may affect stratified analysis.")

            if row_count == 0:
                warnings.append("CSV file exists but contains no data rows.")

    except Exception as e:
        errors.append(f"Error reading CSV file: {str(e)}")

    # Report Results
    if errors:
        logger.error("Validation FAILED with the following errors:")
        for err in errors:
            logger.error(f"  - {err}")
        return False

    if warnings:
        logger.warning("Validation PASSED with warnings:")
        for warn in warnings:
            logger.warning(f"  - {warn}")
    else:
        logger.info("Validation PASSED: Manual CSV is compliant.")

    return True

def main():
    """
    Entry point for the validation script.
    Exits with code 0 on success, 1 on failure.
    """
    setup_logging(level="INFO")
    logger.info("Starting Manual Curation Validation (T063)...")

    success = validate_manual_csv()

    if success:
        logger.info("Validation completed successfully.")
        sys.exit(0)
    else:
        logger.error("Validation failed. Please correct the errors in data/raw/manual_curated.csv.")
        sys.exit(1)

if __name__ == "__main__":
    main()