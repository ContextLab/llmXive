import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from config import ensure_directories, INPUT_PATHS, RANDOM_SEED, SAMPLE_LIMIT, DQS_REQUIRED
from logging_config import get_logger, log_provenance, log_warning

logger = get_logger("config_validation")

def validate_directories():
    """Validate that required directories exist."""
    ensure_directories()
    log_provenance("Directories validated.")

def validate_input_files():
    """Validate that required input files exist."""
    missing = []
    for key, path in INPUT_PATHS.items():
        if not os.path.exists(path):
            missing.append(path)
    
    if missing:
        log_warning(f"Missing input files: {missing}")
        # Do not raise, just log. The pipeline may proceed with available data.
    else:
        log_provenance("All input files present.")

def validate_configuration():
    """Run all configuration validations."""
    validate_directories()
    validate_input_files()

def main():
    """Entry point for config validation."""
    validate_configuration()

if __name__ == "__main__":
    main()
