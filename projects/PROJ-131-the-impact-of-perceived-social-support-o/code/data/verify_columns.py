"""
Task T070b: Verify Data Columns
Inspects the loaded dataset to confirm the presence of the 'platform' column.
Produces column inspection logs and a JSON status report.
"""
import os
import sys
import json
import logging
from pathlib import Path
import yaml

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger
from data.ingestion import load_cyber_data

def verify_platform_column():
    """
    Loads the dataset and verifies the presence of the 'platform' column.
    Writes inspection logs and a JSON status report.
    """
    logger = get_logger("verify_columns")
    logger.info("Starting T070b: Verify Data Columns")

    # Define output paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    results_dir = project_root / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    log_file = results_dir / "column_inspection.log"
    status_file = results_dir / "platform_status.json"

    # Load configuration to get data source
    config_path = project_root / "code" / "config" / "data_sources.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Check if we have a valid source
    if not config or 'dataset_id' not in config:
        raise RuntimeError("E-NO-SOURCE-CONFIG: Data source configuration missing.")

    logger.info(f"Loading dataset from: {config.get('dataset_id')}")

    try:
        # Attempt to load the real data
        # Note: load_cyber_data is expected to raise an error if fetch fails
        # It should NOT fall back to synthetic data.
        df = load_cyber_data()

        if df is None or df.empty:
            raise RuntimeError("E-NO-DATA: Loaded dataset is empty.")

        # 1. Log the full list of column names
        columns = list(df.columns)
        logger.info(f"Columns found: {columns}")

        with open(log_file, 'w') as f:
            f.write(f"Columns found: {columns}\n")
            f.write(f"Total columns: {len(columns)}\n")
            f.write(f"Dataset shape: {df.shape}\n")

        # 2. Check if 'platform' exists
        platform_exists = 'platform' in columns

        # 3. Get unique values if it exists
        platform_categories = []
        if platform_exists:
            platform_categories = sorted(df['platform'].dropna().unique().tolist())
            logger.info(f"Platform column exists. Unique values: {platform_categories}")
        else:
            logger.warning("Platform column NOT found in dataset.")

        # 4. Write status JSON
        status = {
            "platform_exists": platform_exists,
            "platform_categories": platform_categories
        }

        with open(status_file, 'w') as f:
            json.dump(status, f, indent=2)

        logger.info(f"Verification complete. Status written to {status_file}")
        return status

    except Exception as e:
        logger.error(f"Failed to verify columns: {str(e)}")
        # Even on failure, ensure we write a status file indicating the failure state
        # to satisfy the requirement of writing the file.
        failure_status = {
            "platform_exists": False,
            "platform_categories": [],
            "error": str(e)
        }
        with open(status_file, 'w') as f:
            json.dump(failure_status, f, indent=2)
        raise

def main():
    """Entry point for the script."""
    try:
        verify_platform_column()
        print("T070b: Verification successful.")
    except Exception as e:
        print(f"T070b: Verification failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()