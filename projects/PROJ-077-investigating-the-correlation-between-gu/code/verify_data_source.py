"""
Verify Data Source Module.
"""
import os
import sys
from pathlib import Path
from typing import List
from config import INPUT_PATHS, DQS_REQUIRED, ensure_directories
from logging_config import get_logger, log_provenance, log_warning, log_pipeline_start, log_pipeline_end

logger = get_logger("verify_data_source")

def check_local_file_exists(path: str) -> bool:
    return Path(path).exists()

def verify_required_files() -> bool:
    missing = []
    for name, path in INPUT_PATHS.items():
        if not check_local_file_exists(path):
            missing.append(path)
    if missing:
        logger.warning(f"Missing files: {missing}")
        return False
    return True

def verify_data_source_availability() -> bool:
    """Verifies data source availability."""
    log_pipeline_start("verify_data_source")
    if verify_required_files():
        log_pipeline_end("verify_data_source")
        return True
    log_pipeline_end("verify_data_source")
    return False

def main():
    """Entry point."""
    if verify_data_source_availability():
        print("Data source available.")
    else:
        print("Data source unavailable.")
        sys.exit(1)

if __name__ == "__main__":
    main()