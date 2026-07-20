import os
import json
import logging
import pandas as pd
from typing import Dict, Any
from utils.logging import get_logger

logger = get_logger(__name__)

def write_data_status(
    df: pd.DataFrame,
    output_path: str = "data/processed/hea_descriptors.csv",
    status_path: str = "output/data_status.json",
) -> Dict[str, Any]:
    """
    Saves the processed DataFrame to CSV and writes a status JSON file.

    The status JSON includes:
    - count: Total number of samples
    - count_warning: True if count < 500 (data limitation), False otherwise
    - power_status: 'insufficient_power' if count < 50, else 'sufficient_power'

    Args:
        df: The processed DataFrame containing HEA descriptors.
        output_path: Path to save the CSV file.
        status_path: Path to save the status JSON file.

    Returns:
        The status dictionary written to the JSON file.
    """
    logger.info(f"Writing processed data to {output_path}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Write CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Successfully wrote {len(df)} rows to {output_path}")

    count = len(df)
    
    # Determine warnings and power status
    count_warning = count < 500
    if count < 50:
        power_status = "insufficient_power"
        logger.warning(f"INSUFFICIENT_POWER: N={count} < 50")
    else:
        power_status = "sufficient_power"
        logger.info(f"Power analysis: N={count} >= 50")

    status = {
        "count": count,
        "count_warning": count_warning,
        "power_status": power_status
    }

    # Ensure status directory exists
    os.makedirs(os.path.dirname(status_path), exist_ok=True)

    logger.info(f"Writing data status to {status_path}")
    with open(status_path, "w") as f:
        json.dump(status, f, indent=2)

    return status

def main():
    """
    Main entry point for the status writer.
    Expects the processed DataFrame to be passed or loaded from a previous step.
    For this task, we assume the pipeline has already run and produced the data.
    This function is typically called by the pipeline orchestrator.
    """
    # This function is usually called by pipeline.py after processing.
    # If called standalone, it expects a CSV at a specific intermediate location
    # or raises an error if data is missing.
    logger.warning("status_writer.py called as main. Ensure data is passed via pipeline.")

if __name__ == "__main__":
    main()