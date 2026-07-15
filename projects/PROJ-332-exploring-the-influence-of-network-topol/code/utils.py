import logging
import csv
import os
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def setup_logging(level: int = logging.INFO):
    """Configure logging for the pipeline."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('pipeline.log')
        ]
    )
    logger.info("Logging configured")

def write_csv_row(filepath: str, row_data: Dict[str, Any]):
    """Append a row to a CSV file."""
    file_exists = os.path.exists(filepath)
    fieldnames = list(row_data.keys())
    
    with open(filepath, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row_data)
    
    logger.debug(f"Written row to {filepath}")

def format_error(e: Exception) -> str:
    """Format exception for logging."""
    return f"{type(e).__name__}: {str(e)}"
