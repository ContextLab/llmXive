import os
import sys
import json
import logging
from pathlib import Path
import yaml

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logger import setup_logging
from utils.config_loader import load_yaml_config

def verify_platform_column(logger: logging.Logger) -> bool:
    """
    T070b: Verify Data Columns
    
    Action:
    1. Load the dataset from the verified source (via ingestion logic or direct load).
       Since T012 (ingestion) is already completed and T070a-Verify ran, we assume
       the raw data exists at data/raw/cyberbullying_2021.csv (or the path in config).
    2. Log the full list of column names to data/results/column_inspection.log.
    3. Check if 'platform' exists.
    4. Write data/results/platform_status.json with keys:
       - platform_exists (boolean)
       - platform_categories (list of unique values if exists, else [])
    
    Returns:
       True if verification completed successfully (file written), False otherwise.
    """
    # Load configuration to get data paths
    config = load_yaml_config(project_root / "code" / "config" / "data_sources.yaml")
    
    # Determine the raw data file path
    # The config should have 'dataset_id' or 'local_path'. 
    # Based on T071, we expect a verified source. 
    # We will look for the file in data/raw/ as per standard convention.
    raw_data_dir = project_root / "data" / "raw"
    raw_files = list(raw_data_dir.glob("*.csv"))
    
    if not raw_files:
        logger.error("E-NO-RAW-DATA: No CSV files found in data/raw/. Aborting column verification.")
        return False
    
    # Assume the first CSV is the target dataset (Cyberbullying Survey 2021)
    # In a real scenario, we might match by name, but we'll take the first one found.
    target_file = raw_files[0]
    logger.info(f"Loading dataset from: {target_file}")
    
    try:
        import pandas as pd
        df = pd.read_csv(target_file)
    except Exception as e:
        logger.error(f"E-LOAD-FAIL: Failed to load dataset: {e}")
        return False
    
    # 2. Log the full list of column names
    columns = list(df.columns)
    log_path = project_root / "data" / "results" / "column_inspection.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, 'w') as f:
        f.write(f"Dataset: {target_file.name}\n")
        f.write(f"Total Columns: {len(columns)}\n")
        f.write("Columns found: " + ", ".join(columns) + "\n")
        f.write("-" * 50 + "\n")
        for col in columns:
            f.write(f"  - {col}\n")
    
    logger.info(f"Column list logged to: {log_path}")
    
    # 3. Check if 'platform' exists
    platform_exists = 'platform' in columns
    platform_categories = []
    
    if platform_exists:
        # Get unique values (limit to first 50 for log safety if too many)
        unique_vals = df['platform'].dropna().unique().tolist()
        platform_categories = unique_vals[:50] # Store first 50
        if len(unique_vals) > 50:
            platform_categories.append(f"... and {len(unique_vals) - 50} more")
        logger.info(f"Column 'platform' found. Unique values (sample): {platform_categories[:10]}...")
    else:
        logger.warning("Column 'platform' NOT found in dataset.")
    
    # 4. Write platform_status.json
    status = {
        "platform_exists": platform_exists,
        "platform_categories": platform_categories
    }
    
    status_path = project_root / "data" / "results" / "platform_status.json"
    with open(status_path, 'w') as f:
        json.dump(status, f, indent=2)
    
    logger.info(f"Platform status written to: {status_path}")
    logger.info(f"Result: platform_exists={platform_exists}")
    
    return True

def main():
    """Main entry point for T070b."""
    logger = setup_logging("verify_columns")
    logger.info("Starting T070b: Verify Data Columns")
    
    success = verify_platform_column(logger)
    
    if success:
        logger.info("T070b completed successfully.")
    else:
        logger.error("T070b failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()