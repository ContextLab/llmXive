"""
Validate the schema of the real educational dataset fetched in T015.

This script loads a CSV file (default: `data/raw/verified_dataset.csv` or a
provided path argument) and verifies it contains the required columns:
`recommended_categories` and `enrolled_categories`.

If the columns are missing, it raises `DataSchemaError` with the exact message
required by FR-007.

Usage:
    python code/validate_real_data.py [path_to_csv]

If no path is provided, it defaults to the verified dataset from T015.
If a path is provided, it validates that specific file (useful for testing
with mock files like `data/raw/mock_missing_columns.csv`).
"""

import sys
import logging
from pathlib import Path

# Configure logging to output to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path if running as script
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ingestion import DataSchemaError, load_project_data
from config import ProjectConfig

def validate_real_dataset_schema(csv_path: Path):
    """
    Loads the dataset at the given path and validates the required schema.

    Args:
        csv_path: Path to the CSV file to validate.

    Raises:
        DataSchemaError: If required columns are missing.
        FileNotFoundError: If the dataset file does not exist.
    """
    if not csv_path.exists():
        logger.error(f"Dataset file not found at {csv_path}.")
        raise FileNotFoundError(
            f"Dataset not found at {csv_path}. "
            "Please ensure the file exists."
        )

    logger.info(f"Loading dataset from {csv_path}...")
    try:
        df = load_project_data(csv_path)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

    required_columns = {"recommended_categories", "enrolled_categories"}
    available_columns = set(df.columns)

    missing_columns = required_columns - available_columns

    if missing_columns:
        error_msg = (
            f"Required columns {sorted(missing_columns)} missing. "
            "Dataset does not support the specified experimental design."
        )
        logger.error(error_msg)
        raise DataSchemaError(error_msg)

    logger.info("Schema validation successful. Required columns found:")
    logger.info(f"  - {list(required_columns)}")
    logger.info(f"Dataset shape: {df.shape}")
    return True

def main():
    """Main entry point for the validation script."""
    # Determine which file to validate
    if len(sys.argv) > 1:
        target_path = Path(sys.argv[1])
        if not target_path.is_absolute():
            target_path = project_root / target_path
    else:
        config = ProjectConfig()
        target_path = config.data_raw_dir / "verified_dataset.csv"

    try:
        validate_real_dataset_schema(target_path)
        logger.info("Validation PASSED: Dataset schema is correct.")
        return 0
    except DataSchemaError as e:
        logger.error(f"Validation FAILED: {e}")
        return 1
    except FileNotFoundError as e:
        logger.error(f"Validation FAILED: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())