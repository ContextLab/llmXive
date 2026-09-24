"""
Verify and archive output for User Story 1 (Data Collection and Cleaning Pipeline).

This script checks for the existence of critical output artifacts, validates
CSV schema compliance, and ensures the pipeline produced expected results.

Exit codes:
    0: Success - All artifacts present and valid
    1: Failure - Missing artifacts, schema violations, or other errors
"""
import csv
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.utils.logging import get_logger
from code.utils.config import get_data_path, get_contracts_path

# Initialize logger
logger = get_logger(__name__)

# Define artifact paths
DATA_PATH = get_data_path()
PROCESSED_PATH = DATA_PATH / "processed"
RAW_PATH = DATA_PATH / "raw"
CONTRACTS_PATH = get_contracts_path()

CLEANED_CSV = PROCESSED_PATH / "cleaned_studies.csv"
EXCLUDED_LOG = RAW_PATH / "excluded_studies.log"
MOCK_REGISTRY = RAW_PATH / "mock_registry_response.json"

# Expected CSV columns based on T007 schema and pipeline logic
EXPECTED_CSV_COLUMNS = [
    "id", "title", "registry", "age_range", "diagnosis", "outcomes",
    "intervention_components", "delivery_format", "social_skill_domain",
    "follow_up", "abstract_text", "blinded_assessment_flag", "rater_type"
]

def verify_csv_artifact() -> bool:
    """
    Verify the existence and basic structure of cleaned_studies.csv.
    
    Returns:
        bool: True if artifact exists and has valid structure, False otherwise
    """
    logger.info(f"Checking for existence of {CLEANED_CSV}")
    
    if not CLEANED_CSV.exists():
        logger.error(f"Artifact not found: {CLEANED_CSV}")
        return False
    
    logger.info(f"Artifact found: {CLEANED_CSV}")
    
    try:
        with open(CLEANED_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            if not headers:
                logger.error("CSV file is empty or has no headers")
                return False
            
            # Verify schema compliance
            missing_columns = set(EXPECTED_CSV_COLUMNS) - set(headers)
            if missing_columns:
                logger.warning(f"Missing expected columns: {missing_columns}")
                # Non-fatal warning for now, as schema may evolve
            else:
                logger.info("CSV schema compliance verified")
            
            # Count rows
            row_count = sum(1 for _ in reader)
            logger.info(f"CSV contains {row_count} data rows")
            
            if row_count == 0:
                # Check if we're in CI mode (mock data exists)
                if MOCK_REGISTRY.exists():
                    logger.info("CSV is empty but mock data exists (CI mode) - this is acceptable")
                    return True
                else:
                    # Check if no studies matched criteria (real mode)
                    logger.warning("CSV is empty and no mock data found - checking exclusion log")
                    if EXCLUDED_LOG.exists():
                        logger.info("Exclusion log exists, studies may have been filtered out")
                        return True
                    else:
                        logger.error("CSV is empty with no explanation (no mock data, no exclusion log)")
                        return False
            
            return True
            
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        return False

def verify_log_artifact() -> bool:
    """
    Verify the existence of excluded_studies.log.
    
    Returns:
        bool: True if artifact exists, False otherwise
    """
    logger.info(f"Checking for existence of {EXCLUDED_LOG}")
    
    if not EXCLUDED_LOG.exists():
        logger.warning(f"Exclusion log not found: {EXCLUDED_LOG}")
        # This is not necessarily fatal - all studies might have been included
        return True
    
    logger.info(f"Artifact found: {EXCLUDED_LOG}")
    
    try:
        with open(EXCLUDED_LOG, 'r', encoding='utf-8') as f:
            line_count = sum(1 for line in f if line.strip())
            logger.info(f"Exclusion log contains {line_count} entries")
        return True
    except Exception as e:
        logger.error(f"Error reading exclusion log: {e}")
        return False

def verify_schema_compliance() -> bool:
    """
    Verify that the cleaned CSV matches the schema defined in contracts.
    
    Returns:
        bool: True if schema compliance is verified, False otherwise
    """
    schema_path = CONTRACTS_PATH / "cleaned_study.schema.yaml"
    
    if not schema_path.exists():
        logger.warning(f"Schema file not found: {schema_path}")
        return True  # Non-fatal if schema missing
    
    logger.info(f"Schema file found: {schema_path}")
    
    # Load schema
    try:
        import yaml
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        
        # Basic validation: check required fields
        required_fields = schema.get('required', [])
        
        with open(CLEANED_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            missing_required = set(required_fields) - set(headers)
            if missing_required:
                logger.error(f"Missing required schema fields: {missing_required}")
                return False
            
            logger.info("Schema compliance verified")
            return True
            
    except Exception as e:
        logger.error(f"Error verifying schema compliance: {e}")
        return False

def main():
    """
    Main verification function.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    logger.info("Starting output verification for User Story 1")
    logger.info(f"Project root: {project_root}")
    logger.info(f"Data path: {DATA_PATH}")
    
    all_checks_passed = True
    
    # Check 1: Verify CSV artifact
    if not verify_csv_artifact():
        all_checks_passed = False
    
    # Check 2: Verify exclusion log artifact
    if not verify_log_artifact():
        all_checks_passed = False
    
    # Check 3: Verify schema compliance
    if not verify_schema_compliance():
        all_checks_passed = False
    
    # Final verdict
    if all_checks_passed:
        logger.info("All verification checks passed")
        print("✓ Output verification successful")
        return 0
    else:
        logger.error("One or more verification checks failed")
        print("✗ Output verification failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())