import json
import logging
import os
from pathlib import Path
import pandas as pd
from config import get_path

from ingestion import count_raw_records_from_csv, save_raw_record_count, extract_metadata_and_log_exclusions

logger = logging.getLogger(__name__)

def main():
    """
    Task T012b: Count raw records and save to data/results/raw_record_count.json.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    raw_data_path = get_path('data/raw/adress.csv')
    if not raw_data_path.exists():
        logger.error(f"Raw data file not found at {raw_data_path}. Cannot count records.")
        return 1

    try:
        count = count_raw_records_from_csv(raw_data_path)
        logger.info(f"Total raw records: {count}")

        # Load data to extract group counts for logging
        df = pd.read_csv(raw_data_path)
        group_counts = extract_metadata_and_log_exclusions(df, get_path('data/interim/exclusions.log'))

        # Save raw record count
        output_count_path = get_path('data/results/raw_record_count.json')
        save_raw_record_count(count, output_count_path)

        # Save group counts
        group_counts_path = get_path('data/results/group_counts.json')
        os.makedirs(group_counts_path.parent, exist_ok=True)
        with open(group_counts_path, 'w') as f:
            json.dump(group_counts, f, indent=2)

        logger.info("T012b completed: Raw record count and group counts saved.")
        return 0
    except Exception as e:
        logger.error(f"Error in T012b: {e}")
        return 1

if __name__ == "__main__":
    exit(main())