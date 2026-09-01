"""
Final Dataset Validation and Assembly (T017d).

Reads the linkage validation log to determine if village-level aggregation was triggered.
Copies the appropriate source file to the final analysis dataset location.
Validates the final file against the schema contract.
"""
import argparse
import logging
import shutil
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
import yaml

# Import project utilities and constants
from src.config import constants
from src.utils.io_helpers import load_json_strict, write_json_strict, FatalError
from src.config.schemas import validate_dataset_schema, AnalysisDatasetRecord

# Set up logging
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_LOGS = PROJECT_ROOT / "data" / "logs"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

# Input/Output paths
LINKAGE_VALIDATION_PATH = DATA_LOGS / "linkage_validation.json"
AGGREGATED_DATASET_PATH = DATA_PROCESSED / "analysis_dataset_village_aggregated.csv"
FEATURE_ENGINEERED_PATH = DATA_PROCESSED / "feature_engineered_data.csv"
FINAL_DATASET_PATH = DATA_PROCESSED / "analysis_dataset.csv"
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"


def load_linkage_status(validation_path: Path) -> Dict[str, Any]:
    """Load and parse the linkage validation JSON file."""
    if not validation_path.exists():
        raise FileNotFoundError(f"Linkage validation file not found: {validation_path}")
    
    try:
        data = load_json_strict(validation_path)
        return data
    except Exception as e:
        logger.error(f"Failed to load linkage validation JSON: {e}")
        raise


def validate_final_dataset(df: pd.DataFrame, schema_path: Path) -> bool:
    """
    Validate the final dataset against the schema contract.
    Returns True if valid, raises FatalError if invalid.
    """
    if not schema_path.exists():
        logger.warning(f"Schema file not found at {schema_path}. Skipping strict validation.")
        return True

    try:
        # Load schema
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        
        # Perform validation using the project's schema utility
        # The schema expects a list of dicts or a DataFrame
        is_valid, errors = validate_dataset_schema(df, schema)
        
        if not is_valid:
            error_msg = "Schema validation failed:\n" + "\n".join(errors)
            logger.error(error_msg)
            raise FatalError("Final dataset failed schema validation. Check logs for details.")
        
        logger.info("Final dataset passed schema validation.")
        return True

    except Exception as e:
        logger.error(f"Error during schema validation: {e}")
        raise


def assemble_final_dataset(
    triggered_aggregation: bool,
    aggregated_path: Path,
    feature_engineered_path: Path,
    output_path: Path
) -> None:
    """
    Copy the appropriate source file to the final output location.
    """
    source_path = None
    source_name = ""

    if triggered_aggregation:
        source_path = aggregated_path
        source_name = "aggregated dataset"
    else:
        source_path = feature_engineered_path
        source_name = "feature engineered dataset"

    if not source_path.exists():
        raise FileNotFoundError(
            f"Source {source_name} not found at {source_path}. "
            "Ensure the upstream pipeline stage completed successfully."
        )

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Copy file
    logger.info(f"Copying {source_name} from {source_path} to {output_path}")
    shutil.copy2(source_path, output_path)

    if not output_path.exists():
        raise IOError(f"Failed to create final dataset at {output_path}")

    logger.info(f"Final dataset assembled successfully at {output_path}")


def main(args: Optional[list] = None) -> int:
    """
    Main entry point for the final assembly task.
    """
    parser = argparse.ArgumentParser(
        description="T017d: Final Dataset Validation and Assembly"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        default=True,
        help="Run schema validation on the final dataset (default: True)"
    )
    
    parsed_args = parser.parse_args(args)

    try:
        # 1. Load Linkage Status
        logger.info(f"Reading linkage validation from {LINKAGE_VALIDATION_PATH}")
        linkage_data = load_linkage_status(LINKAGE_VALIDATION_PATH)
        
        triggered = linkage_data.get("triggered_aggregation", False)
        logger.info(f"Aggregation triggered: {triggered}")

        # 2. Assemble Final Dataset
        assemble_final_dataset(
            triggered_aggregation=triggered,
            aggregated_path=AGGREGATED_DATASET_PATH,
            feature_engineered_path=FEATURE_ENGINEERED_PATH,
            output_path=FINAL_DATASET_PATH
        )

        # 3. Validate Final Dataset
        if parsed_args.validate:
            logger.info("Validating final dataset against schema...")
            df = pd.read_csv(FINAL_DATASET_PATH)
            validate_final_dataset(df, SCHEMA_PATH)

        logger.info("T017d completed successfully.")
        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except FatalError as e:
        logger.error(f"Fatal error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    sys.exit(main())
