from __future__ import annotations

import logging
import sys
from pathlib import Path
from config import get_all_config, get_processed_dir, get_raw_dir

def validate_output_files() -> None:
    """
    Validates that all required output files exist after pipeline execution.
    This is a critical check for T022 and T021.
    """
    required_files = [
        get_processed_dir() / "clone_metrics.csv",
        get_processed_dir() / "perplexity_scores.csv",
        get_raw_dir() / "github-code-sample.csv"
    ]
    
    missing = []
    for f in required_files:
        if not f.exists():
            missing.append(f)
            
    if missing:
        logging.error(f"Missing required output files: {missing}")
        raise FileNotFoundError(f"Missing required output files: {missing}")
        
    logging.info("All required output files are present.")

def main():
    """Main entry point for validation."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        validate_output_files()
        logging.info("Quickstart validation PASSED.")
    except FileNotFoundError as e:
        logging.error(f"Quickstart validation FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
