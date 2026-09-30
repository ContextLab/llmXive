import sys
import logging
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from code.src.utils.config import get_raw_data_dir, get_project_root
from code.src.utils.validation import load_schema, validate_dataframe_against_schema, validate_dataset
import pandas as pd
import logging

def main():
    """
    Validates the synthetic dataset against the dataset schema contract.
    Ensures strict type enforcement (int, float, bool, enum).
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    project_root = get_project_root()
    data_dir = get_raw_data_dir()
    schema_path = project_root / "code" / "contracts" / "dataset.schema.yaml"
    data_path = data_dir / "synthetic_data.csv"

    logger.info(f"Project Root: {project_root}")
    logger.info(f"Schema Path: {schema_path}")
    logger.info(f"Data Path: {data_path}")

    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        sys.exit(1)

    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        sys.exit(1)

    # Load schema
    logger.info(f"Loading schema from {schema_path}...")
    schema = load_schema(schema_path)

    # Load data
    logger.info(f"Loading data from {data_path}...")
    try:
        df = pd.read_csv(data_path)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)

    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns.")
    logger.info(f"Columns: {list(df.columns)}")

    # Validate
    logger.info("Validating data against schema...")
    try:
        is_valid, errors = validate_dataframe_against_schema(df, schema)
        
        if not is_valid:
            logger.error("Validation FAILED. Errors found:")
            for error in errors:
                logger.error(f"  - {error}")
            sys.exit(1)
        else:
            logger.info("Validation PASSED. All fields match schema types and constraints.")
            # Log a summary of types found
            logger.info("Data Types:")
            for col in df.columns:
                logger.info(f"  {col}: {df[col].dtype}")
            
    except Exception as e:
        logger.error(f"Validation process failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
