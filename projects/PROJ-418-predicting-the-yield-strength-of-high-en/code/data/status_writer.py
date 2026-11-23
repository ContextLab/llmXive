import os
import json
import logging
import pandas as pd
from typing import Dict, Any
from utils.logging import get_logger

logger = get_logger(__name__)

def write_data_status(
    csv_path: str = "data/processed/hea_descriptors.csv",
    output_json: str = "output/data_status.json"
) -> Dict[str, Any]:
    """
    Reads the processed descriptor CSV, counts rows, and writes the status JSON.
    
    Implements the logic from T015:
    1. Count rows in the CSV.
    2. Set count_warning = True if count < 500.
    3. Set power_status = True if count < 50.
    4. Write output/data_status.json with schema:
       { "count": int, "count_warning": bool, "power_status": bool, "timestamp": str }
    
    Args:
        csv_path: Path to the processed CSV file.
        output_json: Path to write the status JSON.
    
    Returns:
        The status dictionary.
    """
    logger.info(f"Reading processed data from {csv_path} to compute status...")
    
    if not os.path.exists(csv_path):
        logger.error(f"Processed data file not found at {csv_path}. Cannot write status.")
        # If the file doesn't exist, we assume 0 count for the status report
        count = 0
    else:
        df = pd.read_csv(csv_path)
        count = len(df)
    
    count_warning = count < 500
    power_status = count < 50
    
    status = {
        "count": count,
        "count_warning": count_warning,
        "power_status": power_status,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_json), exist_ok=True)
    
    logger.info(f"Writing data status to {output_json}: {status}")
    with open(output_json, 'w') as f:
        json.dump(status, f, indent=2)
    
    # Log warnings as required by T015
    if count_warning:
        logger.warning(f"DATA_LIMITATION_WARNING: Only {count} entries found. Statistical power may be reduced.")
    if power_status:
        logger.warning(f"DATA_LIMITATION_WARNING: Only {count} entries found. Statistical power is critically low.")
        
    return status

def main():
    """
    Main entry point for the status writer script.
    Reads the processed descriptors and writes the status JSON.
    """
    try:
        write_data_status(
            csv_path="data/processed/hea_descriptors.csv",
            output_json="output/data_status.json"
        )
        logger.info("Data status written successfully.")
    except Exception as e:
        logger.exception("Failed to write data status")
        raise

if __name__ == "__main__":
    main()
