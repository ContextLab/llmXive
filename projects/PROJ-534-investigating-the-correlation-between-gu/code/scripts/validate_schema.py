"""
Script to validate the synthetic dataset against the defined schema.
This script ensures strict type enforcement (int, float, bool, enum)
and checks for missing values or out-of-range constraints.
"""
import sys
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.src.utils.config import get_raw_data_dir, get_project_root
from code.src.utils.validation import load_schema, validate_dataframe_against_schema, validate_dataset
import pandas as pd

def main():
    """
    Main entry point for schema validation.
    Loads the schema from contracts/dataset.schema.yaml and validates
    the generated synthetic data in data/raw/synthetic_data.csv.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(project_root / "logs" / "validation.log")
        ]
    )
    logger = logging.getLogger("schema_validator")
    logger.info("Starting schema validation for synthetic dataset.")

    # Define paths
    schema_path = project_root / "code" / "contracts" / "dataset.schema.yaml"
    data_path = get_raw_data_dir() / "synthetic_data.csv"

    # Check if files exist
    if not schema_path.exists():
        logger.error(f"Schema file not found at: {schema_path}")
        sys.exit(1)

    if not data_path.exists():
        logger.error(f"Data file not found at: {data_path}")
        sys.exit(1)

    # Load schema
    try:
        schema = load_schema(schema_path)
        logger.info(f"Schema loaded successfully from {schema_path}")
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        sys.exit(1)

    # Load data
    try:
        df = pd.read_csv(data_path)
        logger.info(f"Data loaded successfully from {data_path}. Shape: {df.shape}")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)

    # Validate dataset
    try:
        validation_result = validate_dataset(df, schema)
        
        if validation_result["valid"]:
            logger.info("Validation PASSED: The dataset conforms to the schema.")
            logger.info(f"Details: {validation_result['details']}")
            return 0
        else:
            logger.error("Validation FAILED: The dataset does not conform to the schema.")
            logger.error(f"Details: {validation_result['details']}")
            return 1
    except Exception as e:
        logger.error(f"Validation process failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
