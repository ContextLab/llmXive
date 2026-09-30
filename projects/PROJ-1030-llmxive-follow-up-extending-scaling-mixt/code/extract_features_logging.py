"""
Script to demonstrate the logging and memory usage tracking for feature extraction.
This script simulates the extraction process to generate the required artifacts:
- data/processed/extract.log
- data/processed/memory_log.json
"""
import os
import sys
import json
import time
import logging
import gc
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path to allow imports
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.log_memory import log_memory_usage, get_memory_usage_mb
from utils.logging_config import get_logger

# Constants
DATA_PROCESSED_DIR = project_root / "data" / "processed"
MEMORY_LOG_PATH = str(DATA_PROCESSED_DIR / "memory_log.json")
EXTRACT_LOG_PATH = str(DATA_PROCESSED_DIR / "extract.log")

def setup_logging() -> logging.Logger:
    """Configure the logger for the extraction script."""
    logger = get_logger("feature_extraction")
    
    # Ensure the log file handler exists
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(EXTRACT_LOG_PATH, mode='w')
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Avoid adding duplicate handlers if called multiple times
    if not any(isinstance(h, logging.FileHandler) and h.baseFilename == EXTRACT_LOG_PATH for h in logger.handlers):
        logger.addHandler(file_handler)
    
    return logger

def simulate_extraction_process(logger: logging.Logger) -> List[Dict[str, Any]]:
    """
    Simulate the feature extraction process for a few clips to generate logs.
    In a real scenario, this would call the actual extraction logic.
    """
    log_entries: List[Dict[str, Any]] = []
    clips = [
        ("clip_001", 5),
        ("clip_002", 3),
        ("clip_003", 4)
    ]

    logger.info("Starting feature extraction pipeline.")
    log_memory_usage("pipeline", "start", log_entries, MEMORY_LOG_PATH, logger)

    for clip_id, duration in clips:
        logger.info(f"Processing {clip_id}...")
        log_memory_usage(clip_id, "batch_start", log_entries, MEMORY_LOG_PATH, logger)

        # Simulate processing time
        time.sleep(duration)
        
        # Simulate memory spike
        _ = [i for i in range(1000000)]
        gc.collect()

        log_memory_usage(clip_id, "batch_end", log_entries, MEMORY_LOG_PATH, logger)
        logger.info(f"Finished {clip_id}.")

    log_memory_usage("pipeline", "end", log_entries, MEMORY_LOG_PATH, logger)
    logger.info("Feature extraction pipeline completed.")
    
    return log_entries

def main():
    logger = setup_logging()
    try:
        log_entries = simulate_extraction_process(logger)
        print(f"Successfully generated logs at {EXTRACT_LOG_PATH} and {MEMORY_LOG_PATH}")
        print(f"Total log entries: {len(log_entries)}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
