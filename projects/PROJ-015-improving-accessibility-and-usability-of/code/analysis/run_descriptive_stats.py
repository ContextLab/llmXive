import os
import sys
import pandas as pd
from pathlib import Path
import glob
import json

from analysis.stat_utils import StatUtils
from config.settings import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)

def load_raw_session_data(raw_dir: str) -> list:
    """
    Load all raw session JSON files from the specified directory.
    Returns a list of dictionaries.
    """
    data = []
    if not os.path.exists(raw_dir):
        logger.warning(f"Raw data directory does not exist: {raw_dir}")
        return data
    
    files = glob.glob(os.path.join(raw_dir, "*.json"))
    for f_path in files:
        try:
            with open(f_path, 'r') as f:
                item = json.load(f)
                data.append(item)
        except Exception as e:
            logger.error(f"Error loading {f_path}: {e}")
    return data

def main():
    """
    Main entry point for generating descriptive statistics.
    """
    settings = get_settings()
    raw_dir = settings.data_raw_dir
    output_file = settings.data_processed_dir / "descriptive_stats.csv"
    
    logger.info(f"Starting descriptive stats generation. Raw dir: {raw_dir}, Output: {output_file}")
    
    # Ensure output directory exists
    os.makedirs(settings.data_processed_dir, exist_ok=True)
    
    # Use the StatUtils method to do the heavy lifting
    success = StatUtils.generate_descriptive_stats_csv(
        output_path=str(output_file),
        raw_data_path=str(raw_dir),
        metric="explanation_engagement_time"
    )
    
    if success:
        logger.info("Descriptive stats generation completed successfully.")
    else:
        logger.error("Descriptive stats generation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()