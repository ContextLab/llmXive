import json
import logging
from pathlib import Path
from typing import Dict, Any

from utils.logger import get_logger

logger = get_logger(__name__)

def log_data_source_selection(validation_log_path: str = "data/validation_log.json") -> None:
    """
    Reads the validation log to determine the data source status and logs
    the selection with the specific format required by T016.
    
    If the status is 'SYNTHETIC', it logs an E_DATA_INSUFFICIENT warning.
    
    Args:
        validation_log_path: Path to the validation log JSON file.
    """
    log_path = Path(validation_log_path)
    
    if not log_path.exists():
        logger.error(f"Validation log not found at {validation_log_path}. Cannot log data source selection.")
        return

    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            validation_data: Dict[str, Any] = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse validation log JSON: {e}")
        return

    # Extract relevant fields based on the schema in data/validation_log.json
    source_status = validation_data.get("source_status", "UNKNOWN")
    source_file = validation_data.get("source_file", "UNKNOWN")
    row_count = validation_data.get("row_count", 0)
    
    # Construct the log message as per T016 specification:
    # LOG: Data source selected: {source} | Rows: {count} | Status: {status}
    log_message = f"Data source selected: {source_file} | Rows: {row_count} | Status: {source_status}"
    
    if source_status == "SYNTHETIC":
        logger.warning(f"E_DATA_INSUFFICIENT: Real data validation failed or insufficient. Switching to synthetic mode. {log_message}")
    else:
        logger.info(log_message)

def main() -> None:
    """
    Entry point to execute the logging logic.
    """
    log_data_source_selection()

if __name__ == "__main__":
    main()