import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import get_config, setup_logging

def ensure_deviation_log_exists() -> Path:
    """
    Ensures the deviation log file exists. Creates it if it doesn't.
    """
    config = get_config()
    log_dir = Path(config.get("LOG_DIR", "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / "deviation.log"
    if not path.exists():
        path.touch()
        logging.info(f"Created deviation log at {path}")
    return path

def get_existing_deviations() -> List[str]:
    """
    Reads the deviation log and returns a list of deviation entries (lines).
    """
    path = ensure_deviation_log_exists()
    with open(path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    return lines

def write_deviation_entry(entry: str) -> None:
    """
    Appends a deviation entry to the log file.
    """
    path = ensure_deviation_log_exists()
    with open(path, "a", encoding="utf-8") as f:
        f.write(entry + "\n")
    logging.info(f"Written deviation entry: {entry}")

def consolidate_deviation_log() -> None:
    """
    Consolidates the deviation log by ensuring all required deviations are present.
    This function checks for FR-002 and FR-003 and adds them if missing.
    """
    required_deviations = {
        "FR-002": "ISRIC merge excluded due to lack of verified source",
        "FR-003": "KNN imputation excluded to preserve statistical validity; missing nutrients are excluded"
    }
    
    existing_lines = get_existing_deviations()
    existing_ids = set()
    
    # Parse existing lines to extract IDs if they follow the pattern "FR-XXX: ..."
    for line in existing_lines:
        if line.startswith("FR-"):
            parts = line.split(":")
            if len(parts) >= 1:
                existing_ids.add(parts[0].strip())
    
    # Add missing deviations
    for dev_id, description in required_deviations.items():
        if dev_id not in existing_ids:
            write_deviation_entry(f"{dev_id}: {description}")
        else:
            logging.info(f"Deviation {dev_id} already exists in log")

def main() -> None:
    """
    Main entry point for consolidating the deviation log.
    """
    config = get_config()
    logger = setup_logging(config)
    
    logger.info("Starting deviation log consolidation")
    consolidate_deviation_log()
    logger.info("Deviation log consolidation complete")

if __name__ == "__main__":
    main()