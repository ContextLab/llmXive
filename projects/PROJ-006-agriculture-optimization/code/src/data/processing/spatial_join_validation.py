"""
T017c: Perform Spatial Join Validation and Aggregation Trigger.

Reads linkage_validation.json (output of T017), counts valid households in raw survey,
calculates linkage percentage, and triggers aggregation (T021) if needed.
"""
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd

# Import logging setup from io_helpers
# Note: The API surface shows setup_logging exists in src.utils.io_helpers
from src.utils.io_helpers import setup_logging

# Constants for file paths (relative to project root)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_LOGS_DIR = PROJECT_ROOT / "data" / "logs"

SURVEY_RAW_PATH = DATA_RAW_DIR / "survey_raw.csv"
SPATIAL_JOINED_PATH = DATA_PROCESSED_DIR / "spatial_joined_data.csv"
LINKAGE_VALIDATION_PATH = DATA_LOGS_DIR / "linkage_validation.json"

# Setup logging using the standard utility
# The previous error was caused by passing a string like "synthetic_generator" as log level.
# We must pass a valid log level string (e.g., "INFO") or use the default.
logger = setup_logging("T017c_spatial_join_validation", level="INFO")


def load_linkage_validation() -> Dict[str, Any]:
    """Load and validate linkage_validation.json."""
    if not LINKAGE_VALIDATION_PATH.exists():
        logger.error(f"Linkage validation file not found: {LINKAGE_VALIDATION_PATH}")
        raise FileNotFoundError(f"Missing required file: {LINKAGE_VALIDATION_PATH}")

    try:
        with open(LINKAGE_VALIDATION_PATH, 'r') as f:
            data = json.load(f)
        
        # Validate required keys exist
        required_keys = ['linkage_percentage', 'total_valid_households', 'triggered_aggregation']
        for key in required_keys:
            if key not in data:
                logger.error(f"Linkage validation file missing required key: {key}")
                raise ValueError(f"Invalid linkage_validation.json: missing key '{key}'")
        
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse linkage_validation.json: {e}")
        raise


def count_valid_households_in_raw_survey() -> int:
    """
    Count rows where latitude and longitude are not null in data/raw/survey_raw.csv.
    Definition: total_valid_households = count of records with non-null coordinates.
    """
    if not SURVEY_RAW_PATH.exists():
        logger.error(f"Raw survey file not found: {SURVEY_RAW_PATH}")
        raise FileNotFoundError(f"Missing required file: {SURVEY_RAW_PATH}")

    try:
        df = pd.read_csv(SURVEY_RAW_PATH)
        
        # Check for required columns
        if 'latitude' not in df.columns or 'longitude' not in df.columns:
            logger.error(f"Raw survey file missing required columns (latitude, longitude)")
            raise ValueError(f"Invalid survey_raw.csv: missing required columns")

        # Count rows where both latitude and longitude are not null
        valid_mask = df['latitude'].notna() & df['longitude'].notna()
        count = valid_mask.sum()
        
        logger.info(f"Total valid households in raw survey: {count}")
        return int(count)
    except Exception as e:
        logger.error(f"Failed to process raw survey data: {e}")
        raise


def count_matched_households() -> int:
    """
    Count rows in spatial_joined_data.csv where household_id exists in survey_raw.csv.
    """
    if not SPATIAL_JOINED_PATH.exists():
        logger.error(f"Spatial joined file not found: {SPATIAL_JOINED_PATH}")
        raise FileNotFoundError(f"Missing required file: {SPATIAL_JOINED_PATH}")
    
    if not SURVEY_RAW_PATH.exists():
        logger.error(f"Raw survey file not found: {SURVEY_RAW_PATH}")
        raise FileNotFoundError(f"Missing required file: {SURVEY_RAW_PATH}")

    try:
        # Load spatial joined data
        df_joined = pd.read_csv(SPATIAL_JOINED_PATH)
        
        # Load raw survey to get valid household IDs
        df_survey = pd.read_csv(SURVEY_RAW_PATH)
        valid_household_ids = set(df_survey['household_id'].dropna().unique())
        
        # Count matched households
        matched_count = df_joined['household_id'].isin(valid_household_ids).sum()
        
        logger.info(f"Matched households in spatial join: {matched_count}")
        return int(matched_count)
    except Exception as e:
        logger.error(f"Failed to calculate matched households: {e}")
        raise


def trigger_aggregation_routine():
    """
    If triggered_aggregation is true in the log, trigger the aggregation routine defined in T021.
    This calls the main function of feature_engineering.py which handles aggregation logic.
    """
    logger.info("Triggering aggregation routine (T021)...")
    
    try:
        # Import and run the feature engineering aggregation logic
        from src.data.processing.feature_engineering import main as feature_engineering_main
        
        # Run with arguments to trigger aggregation check
        # The feature_engineering.py main function should handle the logic based on linkage_validation.json
        sys.argv = ['feature_engineering.py', '--aggregate']
        feature_engineering_main()
        
        logger.info("Aggregation routine completed successfully.")
    except Exception as e:
        logger.error(f"Aggregation routine failed: {e}")
        raise


def run_validation():
    """
    Main validation logic for T017c.
    1. Read linkage_validation.json
    2. Count total_valid_households from raw survey
    3. Calculate linkage percentage
    4. Handle errors and trigger aggregation if needed
    """
    logger.info("Starting spatial join validation (T017c)...")
    
    # Step 1: Load linkage validation data
    try:
        linkage_data = load_linkage_validation()
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load linkage validation: {e}")
        return 1

    # Step 2: Count valid households in raw survey
    try:
        total_valid_households = count_valid_households_in_raw_survey()
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to count valid households: {e}")
        return 1

    # Error Handling: If total_valid_households is 0, log FATAL_NO_HOUSEHOLDS and exit
    if total_valid_households == 0:
        logger.critical("FATAL_NO_HOUSEHOLDS: No households with valid coordinates found in raw survey.")
        return 1

    # Step 3: Calculate linkage percentage
    try:
        matched_households = count_matched_households()
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to count matched households: {e}")
        return 1

    linkage_percentage = (matched_households / total_valid_households) * 100 if total_valid_households > 0 else 0.0
    logger.info(f"Linkage percentage: {linkage_percentage:.2f}% ({matched_households}/{total_valid_households})")

    # Step 4: Check if aggregation is triggered
    triggered_aggregation = linkage_data.get('triggered_aggregation', False)
    
    if triggered_aggregation:
        logger.info("Aggregation triggered (linkage < 95% or N < 300). Executing aggregation routine.")
        try:
            trigger_aggregation_routine()
        except Exception as e:
            logger.error(f"Aggregation routine failed: {e}")
            return 1
        logger.info("Aggregation completed successfully.")
    else:
        logger.info("Aggregation not triggered. Linkage validation passed.")

    # Log any exclusion reasons if present
    exclusion_reason = linkage_data.get('exclusion_reason', None)
    if exclusion_reason:
        logger.warning(f"Exclusion reason from linkage validation: {exclusion_reason}")
    
    logger.info("Spatial join validation (T017c) completed successfully.")
    return 0


def main():
    """CLI entry point for T017c."""
    parser = argparse.ArgumentParser(
        description="Perform spatial join validation and trigger aggregation if needed."
    )
    parser.add_argument(
        '--log-level', 
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], 
        default='INFO',
        help='Set the logging level'
    )
    
    args = parser.parse_args()
    
    # Re-setup logging with the specified level
    # The previous error was "Invalid log level: synthetic_generator" because a module name was passed.
    # We ensure we pass a valid log level string here.
    global logger
    logger = setup_logging("T017c_spatial_join_validation", level=args.log_level)
    
    try:
        exit_code = run_validation()
        sys.exit(exit_code)
    except Exception as e:
        logger.critical(f"Unexpected error during validation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()