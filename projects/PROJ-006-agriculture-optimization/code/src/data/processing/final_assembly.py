"""
Final Dataset Validation and Assembly (T017d).

Logic:
1. Read data/logs/linkage_validation.json.
2. If triggered_aggregation is true:
   - Copy data/processed/analysis_dataset_village_aggregated.csv to data/processed/analysis_dataset.csv.
3. Otherwise:
   - Copy data/processed/feature_engineered_data.csv to data/processed/analysis_dataset.csv.
4. Validate the final file against the dataset schema.
"""

import argparse
import json
import logging
import shutil
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Import from sibling modules using the provided API surface
from src.utils.io_helpers import setup_logging, load_json_strict, write_json_strict, FatalError
from src.config.schemas import validate_dataset_schema

# Setup logging
logger = setup_logging("final_assembly")

# Constants
LINKAGE_VALIDATION_PATH = Path("data/logs/linkage_validation.json")
AGGREGATED_DATASET_PATH = Path("data/processed/analysis_dataset_village_aggregated.csv")
FEATURE_ENGINEERED_PATH = Path("data/processed/feature_engineered_data.csv")
FINAL_DATASET_PATH = Path("data/processed/analysis_dataset.csv")
SCHEMA_PATH = Path("contracts/dataset.schema.yaml")


def load_linkage_status() -> Dict[str, Any]:
    """Load and parse the linkage validation JSON."""
    if not LINKAGE_VALIDATION_PATH.exists():
        raise FileNotFoundError(
            f"Linkage validation file not found at {LINKAGE_VALIDATION_PATH}. "
            "Run spatial_join.py and T017c first."
        )
    return load_json_strict(LINKAGE_VALIDATION_PATH)


def validate_final_dataset() -> bool:
    """
    Validate the final assembled dataset against the schema.
    Returns True if valid, raises FatalError if invalid.
    """
    if not FINAL_DATASET_PATH.exists():
        raise FatalError(f"Final dataset not found at {FINAL_DATASET_PATH}")

    logger.info(f"Validating {FINAL_DATASET_PATH} against {SCHEMA_PATH}...")
    try:
        valid, errors = validate_dataset_schema(FINAL_DATASET_PATH, SCHEMA_PATH)
        if not valid:
            logger.error("Schema validation failed:")
            for err in errors:
                logger.error(f"  - {err}")
            raise FatalError("Final dataset failed schema validation.")
        logger.info("Schema validation passed.")
        return True
    except Exception as e:
        logger.exception("Unexpected error during validation")
        raise FatalError(f"Validation failed with exception: {e}")


def assemble_final_dataset() -> None:
    """
    Main logic to assemble the final dataset based on linkage status.
    """
    logger.info("Starting final dataset assembly (T017d)...")

    # Step 1: Read linkage validation status
    try:
        linkage_status = load_linkage_status()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)

    triggered_aggregation = linkage_status.get("triggered_aggregation", False)
    logger.info(f"Triggered aggregation: {triggered_aggregation}")

    # Step 2: Determine source and copy
    if triggered_aggregation:
        source_path = AGGREGATED_DATASET_PATH
        logger.info(f"Aggregation triggered. Copying {source_path} -> {FINAL_DATASET_PATH}")
        if not source_path.exists():
            raise FatalError(
                f"Aggregated dataset not found at {source_path}. "
                "Run T021 (village aggregation) first."
            )
    else:
        source_path = FEATURE_ENGINEERED_PATH
        logger.info(f"Aggregation not triggered. Copying {source_path} -> {FINAL_DATASET_PATH}")
        if not source_path.exists():
            raise FatalError(
                f"Feature engineered dataset not found at {source_path}. "
                "Run T018b (feature engineering) first."
            )

    # Ensure destination directory exists
    FINAL_DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Copy file
    shutil.copy2(source_path, FINAL_DATASET_PATH)
    logger.info(f"Successfully copied {source_path.name} to {FINAL_DATASET_PATH.name}")

    # Step 3: Validate
    try:
        validate_final_dataset()
    except FatalError as e:
        logger.error(str(e))
        sys.exit(1)

    logger.info("Final dataset assembly and validation complete.")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Final Dataset Assembly (T017d)")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level"
    )
    args = parser.parse_args()

    # Re-setup logging with the requested level
    global logger
    logger = setup_logging("final_assembly", args.log_level)

    try:
        assemble_final_dataset()
    except Exception as e:
        logger.exception("Fatal error in final assembly")
        sys.exit(1)


if __name__ == "__main__":
    main()
