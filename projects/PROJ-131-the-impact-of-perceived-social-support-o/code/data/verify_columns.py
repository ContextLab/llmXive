"""
T012b: Verify Platform Column in Ingested Dataset.

This script loads the Cyberbullying Survey 2021 dataset (via the verified ingestion logic)
and checks for the existence of the 'platform' column.

It updates data/results/platform_status.json with the verification results.
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add parent directory to path to allow imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from data.ingestion import load_cyber_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

RESULTS_DIR = project_root / "data" / "results"
OUTPUT_FILE = RESULTS_DIR / "platform_status.json"

def verify_platform_column():
    """
    Load the dataset and verify the presence of the 'platform' column.
    Saves the result to data/results/platform_status.json.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        logger.info("Loading Cyberbullying Survey 2021 dataset to verify columns...")
        # This function is expected to load the REAL data from the verified source (UCI ID 123)
        # or raise an error if it fails, preventing synthetic fallback.
        df = load_cyber_data()
        
        if df is None or df.empty:
            logger.error("Dataset loaded but is empty. Cannot verify columns.")
            raise RuntimeError("E-EMPTY-DATA-001: Dataset loaded but contains no rows.")

        columns = df.columns.tolist()
        logger.info(f"Dataset columns: {columns}")

        platform_exists = 'platform' in columns
        platform_categories = []

        if platform_exists:
            # Get unique values, handling potential NaNs
            unique_vals = df['platform'].dropna().unique().tolist()
            platform_categories = [str(v) for v in unique_vals]
            logger.info(f"Found 'platform' column. Unique values: {platform_categories}")
        else:
            logger.warning("'platform' column NOT found in the dataset.")

        result = {
            "platform_exists": platform_exists,
            "platform_categories": platform_categories,
            "total_rows": len(df),
            "total_columns": len(columns),
            "source_verified": True
        }

        with open(OUTPUT_FILE, 'w') as f:
            json.dump(result, f, indent=2)

        logger.info(f"Verification complete. Results saved to {OUTPUT_FILE}")
        
        if not platform_exists:
            # According to task T027b, if missing, we log a warning and skip stratification.
            # However, for this specific task T012b, we just report the status.
            logger.warning("W-NO-PLATFORM-001: Platform column missing. Stratification analyses will be skipped.")

        return result

    except Exception as e:
        logger.error(f"Failed to verify platform column: {e}")
        # Re-raise to ensure the pipeline halts if data cannot be loaded
        raise

def main():
    """Entry point for T012b."""
    verify_platform_column()

if __name__ == "__main__":
    main()
