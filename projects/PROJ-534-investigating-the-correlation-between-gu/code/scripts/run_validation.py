"""
Script to run the validation of the synthetic dataset against the schema.
This script is intended to be run as part of the pipeline to ensure data integrity.
"""
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.src.utils.config import get_raw_data_dir, get_project_root
from code.src.utils.validation import load_schema, validate_dataframe_against_schema, validate_dataset
import pandas as pd

def main():
    """
    Main entry point for running validation.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(project_root / "logs" / "validation_run.log")
        ]
    )
    logger = logging.getLogger("validation_runner")
    logger.info("Starting validation run.")

    # Define paths
    schema_path = project_root / "code" / "contracts" / "dataset.schema.yaml"
    data_path = get_raw_data_dir() / "synthetic_data.csv"

    # Check files
    if not schema_path.exists():
        logger.error(f"Schema not found: {schema_path}")
        return 1
    if not data_path.exists():
        logger.error(f"Data not found: {data_path}")
        return 1

    # Load
    try:
        schema = load_schema(schema_path)
        df = pd.read_csv(data_path)
    except Exception as e:
        logger.error(f"Failed to load resources: {e}")
        return 1

    # Validate
    result = validate_dataset(df, schema)

    if result["valid"]:
        logger.info("SUCCESS: Dataset is valid.")
        return 0
    else:
        logger.error("FAILURE: Dataset is invalid.")
        for detail in result["details"]:
            logger.error(f"  - {detail}")
        return 1

if __name__ == "__main__":
    sys.exit(main())