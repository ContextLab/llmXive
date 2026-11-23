import os
import sys
import logging
import pandas as pd
from pathlib import Path

from config import get_data_path, setup_logging

logger = logging.getLogger(__name__)

def validate_baseline() -> bool:
    """Validates the static baseline CSV."""
    path = get_data_path("static_baseline.csv")
    if not os.path.exists(path):
        logger.error(f"File not found: {path}")
        return False
    
    df = pd.read_csv(path)
    required_cols = ["code", "loc", "cyclomatic_complexity", "static_smell_labels"]
    
    if not all(col in df.columns for col in required_cols):
        logger.error("Missing required columns.")
        return False
    
    if len(df) < 100:
        logger.warning("Dataset size is small.")
    
    return True

def main():
    setup_logging()
    if validate_baseline():
        logger.info("Baseline validation passed.")
    else:
        logger.error("Baseline validation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
