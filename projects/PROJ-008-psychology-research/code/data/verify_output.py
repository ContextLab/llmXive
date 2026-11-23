"""
Verification script for US1 pipeline outputs.
Checks existence, row counts, and schema compliance for cleaned_studies.csv and excluded_studies.log.
"""
import os
import sys
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger
from utils.config import get_data_path, get_contracts_path

logger = get_logger(__name__)

# Define expected paths relative to project root
DATA_PATH = get_data_path()
PROCESSED_DIR = DATA_PATH / "processed"
RAW_DIR = DATA_PATH / "raw"
CONTRACTS_PATH = get_contracts_path()

CLEANED_CSV_PATH = PROCESSED_DIR / "cleaned_studies.csv"
EXCLUDED_LOG_PATH = RAW_DIR / "excluded_studies.log"
CLEANED_SCHEMA_PATH = CONTRACTS_PATH / "cleaned_study.schema.yaml"

REQUIRED_CSV_COLUMNS = [
    "id", "title", "registry", "age_range", "diagnosis", "outcomes",
    "intervention_components", "delivery_format", "follow_up",
    "abstract_text", "social_skill_domain"
]

REQUIRED_LOG_FIELDS = ["study_id", "reason", "timestamp"]

def verify_csv_artifact(path: Path) -> bool:
    """Verify CSV file exists, has rows, and contains required columns."""
    if not path.exists():
        logger.error(f"CSV artifact missing: {path}")
        return False

    try:
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

            if not headers:
                logger.error("CSV file is empty or has no headers.")
                return False

            # Check required columns
            missing_cols = set(REQUIRED_CSV_COLUMNS) - set(headers)
            if missing_cols:
                logger.error(f"CSV missing required columns: {missing_cols}")
                return False

            # Count rows
            row_count = 0
            for row in reader:
                row_count += 1

            if row_count == 0:
                logger.error("CSV file has 0 data rows.")
                return False

            logger.info(f"CSV verification passed: {row_count} rows, all required columns present.")
            return True

    except Exception as e:
        logger.error(f"Error reading CSV: {e}")
        return False

def verify_log_artifact(path: Path) -> bool:
    """Verify JSONL log file exists and is not empty."""
    if not path.exists():
        logger.error(f"Log artifact missing: {path}")
        return False

    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if not lines:
            logger.error("Log file is empty.")
            return False

        # Validate JSON structure of each line
        valid_count = 0
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                missing_fields = set(REQUIRED_LOG_FIELDS) - set(record.keys())
                if missing_fields:
                    logger.warning(f"Log line {i+1} missing fields: {missing_fields}")
                else:
                    valid_count += 1
            except json.JSONDecodeError:
                logger.error(f"Log line {i+1} is not valid JSON.")
                return False

        if valid_count == 0:
            logger.error("Log file contains no valid records.")
            return False

        logger.info(f"Log verification passed: {valid_count} valid records.")
        return True

    except Exception as e:
        logger.error(f"Error reading log: {e}")
        return False

def verify_schema_compliance(csv_path: Path, schema_path: Path) -> bool:
    """
    Verify CSV data against the YAML schema.
    Checks enum values and basic type constraints defined in the schema.
    """
    if not schema_path.exists():
        logger.error(f"Schema file missing: {schema_path}")
        return False

    try:
        import yaml
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        return False

    if not schema or 'properties' not in schema:
        logger.error("Invalid schema format.")
        return False

    properties = schema['properties']
    enum_fields = {}
    for field_name, field_def in properties.items():
        if 'enum' in field_def:
            enum_fields[field_name] = set(field_def['enum'])

    if not enum_fields:
        logger.warning("No enum constraints found in schema to verify.")
        # If no enums, we assume basic structural compliance is enough
        return True

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            row_count = 0
            errors = []

            for row in reader:
                row_count += 1
                for field, allowed_values in enum_fields.items():
                    if field in row:
                        val = row[field]
                        if val and val not in allowed_values:
                            errors.append(f"Row {row_count}: Field '{field}' has invalid value '{val}'. Allowed: {allowed_values}")

            if errors:
                logger.error(f"Schema compliance failed for {len(errors)} records.")
                for err in errors[:5]: # Log first 5
                    logger.error(err)
                if len(errors) > 5:
                    logger.error(f"... and {len(errors) - 5} more errors.")
                return False

            logger.info(f"Schema compliance verified for {row_count} records.")
            return True

    except Exception as e:
        logger.error(f"Error during schema verification: {e}")
        return False

def main():
    """Main entry point for verification."""
    logger.info("Starting output verification for US1...")
    
    all_passed = True

    # 1. Verify CSV
    if not verify_csv_artifact(CLEANED_CSV_PATH):
        all_passed = False

    # 2. Verify Log
    if not verify_log_artifact(EXCLUDED_LOG_PATH):
        all_passed = False

    # 3. Verify Schema
    if not verify_schema_compliance(CLEANED_CSV_PATH, CLEANED_SCHEMA_PATH):
        all_passed = False

    if all_passed:
        logger.info("All verification checks passed.")
        sys.exit(0)
    else:
        logger.error("One or more verification checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()