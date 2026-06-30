#!/usr/bin/env python3
"""Dataset integrity checks and logging for PROJ-601."""

import csv
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/validation.log')
    ]
)
logger = logging.getLogger(__name__)


def stream_csv(file_path: str, chunk_size: int = 1000):
    """Yield rows from a CSV file in chunks to ensure memory efficiency (<7 GB RAM).

    This generator approach prevents loading the entire dataset into memory at once,
    adhering to FR-006.
    """
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row

def validate_csv_integrity(file_path: str, required_columns: List[str]) -> bool:
    """Check if a CSV file has required columns and non-empty rows."""
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False

    try:
        # Use streaming logic to handle large files without loading them entirely into memory
        headers = None
        row_count = 0
        first_chunk = True
        
        for row in stream_csv(file_path):
            if first_chunk:
                headers = row.keys()
                if not headers:
                    logger.error(f"No headers found in {file_path}")
                    return False
                
                missing = set(required_columns) - set(headers)
                if missing:
                    logger.error(f"Missing columns in {file_path}: {missing}")
                    return False
                first_chunk = False
            row_count += 1
            
            # Optional: Log progress for very large files
            if row_count % 10000 == 0:
                logger.info(f"Processed {row_count} rows...")
        
        if row_count == 0:
            logger.warning(f"File {file_path} is empty (0 rows)")
        else:
            logger.info(f"Validated {file_path}: {row_count} rows, columns: {list(headers)}")
            return True
    except Exception as e:
        logger.error(f"Error validating {file_path}: {e}")
        return False

if __name__ == "__main__":
    # Example usage for data/results.csv
    validate_csv_integrity("data/results.csv", ["id", "score"])
    validate_csv_integrity("data/summary.csv", ["metric", "value"])
