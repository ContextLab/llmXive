import os
import logging
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd

from utils import setup_logging, retry_on_failure, DataFetchError
from config import get_config
import api_config

# Ensure logger is configured
logger = setup_logging("download")

def count_unique_planets(metadata_path: str = None) -> int:
    """
    Count unique planets from the saved metadata.csv.
    
    Args:
        metadata_path: Path to the metadata CSV file. Defaults to 
                       data/processed/metadata.csv from config.
    
    Returns:
        int: The count of unique planets.
    
    Raises:
        FileNotFoundError: If the metadata file does not exist.
        ValueError: If the file is empty or lacks the 'planet_name' column.
    """
    config = get_config()
    if metadata_path is None:
        metadata_path = str(config.data_dir / "processed" / "metadata.csv")
    
    path = Path(metadata_path)
    if not path.exists():
        raise FileNotFoundError(f"Metadata file not found at {metadata_path}")
    
    logger.info(f"Loading metadata from {metadata_path} to count unique planets")
    df = pd.read_csv(metadata_path)
    
    if 'planet_name' not in df.columns:
        raise ValueError("Metadata file missing required 'planet_name' column")
    
    unique_count = df['planet_name'].nunique()
    logger.info(f"Found {unique_count} unique planets in {metadata_path}")
    
    return unique_count

def save_count_report(count: int, output_path: str = None) -> None:
    """
    Save the unique planet count to a JSON report file.
    
    Args:
        count: The integer count of unique planets.
        output_path: Path to the output JSON file. Defaults to 
                     data/processed/count_report.json.
    """
    config = get_config()
    if output_path is None:
        output_path = str(config.data_dir / "processed" / "count_report.json")
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        "count": count
    }
    
    with open(path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Saved count report to {output_path}: {report}")

def main():
    """
    Main entry point for T013a: Count unique planets and save report.
    This function is called by the pipeline orchestrator.
    """
    logger.info("Starting T013a: Count unique planets")
    
    try:
        # 1. Count unique planets from metadata.csv
        count = count_unique_planets()
        
        # 2. Save the report to data/processed/count_report.json
        save_count_report(count)
        
        logger.info("T013a completed successfully")
        return 0
    except Exception as e:
        logger.error(f"T013a failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())