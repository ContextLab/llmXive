"""
Script to validate the generated synthetic data against the dataset schema.
This implements task T010: Validate Synthetic Data.
"""
import sys
import logging
from pathlib import Path

# Adjust path to ensure imports work when run from root or code/
# The API surface indicates imports from code.src.utils...
# Assuming the script is run from the project root, we need to ensure 'code' is in sys.path
# However, the provided surface shows `from code.scripts.validate_schema import main`
# and `from code.src.utils.config import ...`
# This implies the project root is the parent of 'code'.
# We will add the current working directory to sys.path if 'code' is not found,
# but standard practice for this layout is to run from root.
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.utils.config import get_raw_data_dir, get_project_root
from code.src.utils.validation import load_schema, validate_dataframe_against_schema, validate_dataset
import pandas as pd
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for schema validation.
    Loads the synthetic data from data/raw/synthetic_data.csv
    and validates it against contracts/dataset.schema.yaml.
    """
    logger.info("Starting synthetic data validation (Task T010)...")

    # Get paths
    project_root = get_project_root()
    data_dir = get_raw_data_dir()
    schema_path = project_root / "contracts" / "dataset.schema.yaml"
    data_path = data_dir / "synthetic_data.csv"

    logger.info(f"Project root: {project_root}")
    logger.info(f"Schema path: {schema_path}")
    logger.info(f"Data path: {data_path}")

    # Check if files exist
    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        sys.exit(1)

    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}. Please run T009 first.")
        sys.exit(1)

    # Load schema
    logger.info(f"Loading schema from {schema_path}...")
    try:
        schema = load_schema(schema_path)
        logger.info("Schema loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        sys.exit(1)

    # Load data
    logger.info(f"Loading data from {data_path}...")
    try:
        df = pd.read_csv(data_path)
        logger.info(f"Data loaded. Shape: {df.shape}")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        sys.exit(1)

    # Validate
    logger.info("Validating data against schema...")
    is_valid, errors = validate_dataframe_against_schema(df, schema)

    if is_valid:
        logger.info("✅ Validation PASSED. All data types and constraints match the schema.")
        return 0
    else:
        logger.error("❌ Validation FAILED.")
        for error in errors:
            logger.error(f"  - {error}")
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())