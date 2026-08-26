"""
Pipeline script to run the validation step (T018) on the generated features.csv.
This script must be run after T017 generates the CSV but before the final artifact is accepted.
It ensures no NaN values exist in metric columns.
"""
import sys
import os
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "code"))

from src.validate_metrics import validate_schema_and_metrics
from src.config import get_memory_limit_bytes

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    features_path = project_root / "code" / "data" / "processed" / "features.csv"
    
    if not features_path.exists():
        logger.error(f"Features file not found at {features_path}. Run T017 first.")
        sys.exit(1)
    
    logger.info(f"Validating {features_path}...")
    
    try:
        import pandas as pd
        df = pd.read_csv(features_path)
        
        # Run the strict validation
        validate_schema_and_metrics(df, features_path)
        
        logger.info("Validation PASSED. No NaN values in metric columns.")
        logger.info("The features.csv is ready for downstream tasks (T021+).")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Validation FAILED: {e}")
        logger.error("The features.csv contains invalid data (NaNs, missing columns, etc.).")
        logger.error("Please fix the upstream data generation scripts (T013-T017).")
        sys.exit(1)

if __name__ == "__main__":
    main()