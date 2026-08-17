"""
T015d: Validate Dataset Quantization Levels

Loads the generated training dataset (training_sample.parquet) and verifies that
samples for all three required quantization levels (INT4, INT8, FP8) are present
and sufficiently represented.

This script FAILS LOUDLY if:
1. The input file does not exist.
2. Any of the three levels (INT4, INT8, FP8) are missing entirely.
3. Any level has fewer than 10% of the total samples (under-represented).

This ensures SC-004 (Multi-level coverage) is met before proceeding to training.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

# Configuration constants
REQUIRED_LEVELS: List[str] = ["INT4", "INT8", "FP8"]
MIN_LEVEL_RATIO: float = 0.10  # 10% of total samples
INPUT_FILE_PATH: str = "data/processed/training_sample.parquet"
LOG_FILE_PATH: str = "logs/pipeline.log"

def setup_logger() -> logging.Logger:
    """Sets up a basic logger for this script."""
    logger = logging.getLogger("T015d_ValidateLevels")
    logger.setLevel(logging.INFO)
    
    # Ensure log directory exists
    log_dir = Path(LOG_FILE_PATH).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # File handler
    fh = logging.FileHandler(LOG_FILE_PATH)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)

    # Avoid duplicate handlers if logger is reused
    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(ch)
    
    return logger

def load_dataset(file_path: str, logger: logging.Logger) -> pd.DataFrame:
    """
    Loads the parquet dataset.
    Raises FileNotFoundError if the file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        logger.error(f"Input file not found: {path.absolute()}")
        raise FileNotFoundError(f"Dataset file not found at {path.absolute()}")
    
    logger.info(f"Loading dataset from {path.absolute()}")
    try:
        df = pd.read_parquet(path)
    except Exception as e:
        logger.error(f"Failed to load parquet file: {e}")
        raise
    
    logger.info(f"Dataset loaded successfully. Total rows: {len(df)}")
    return df

def validate_levels(df: pd.DataFrame, logger: logging.Logger) -> Tuple[bool, Dict[str, float]]:
    """
    Validates that all required quantization levels are present and meet the minimum ratio.
    
    Returns:
        Tuple[bool, Dict]: (is_valid, level_counts_ratio)
        Raises SystemExit if validation fails.
    """
    if df.empty:
        logger.error("Dataset is empty. Cannot validate levels.")
        raise SystemExit("FATAL: Dataset is empty.")

    total_samples = len(df)
    
    # Check if the column exists
    if "quantization_level" not in df.columns:
        logger.error("Column 'quantization_level' not found in dataset.")
        raise SystemExit("FATAL: Missing 'quantization_level' column.")

    # Calculate counts and ratios
    counts = df["quantization_level"].value_counts().to_dict()
    ratios = {level: (counts.get(level, 0) / total_samples) for level in REQUIRED_LEVELS}
    
    logger.info(f"Total samples: {total_samples}")
    logger.info(f"Sample counts per level: {counts}")
    
    missing_levels = []
    under_represented_levels = []

    for level in REQUIRED_LEVELS:
        count = counts.get(level, 0)
        ratio = ratios[level]
        
        if count == 0:
            missing_levels.append(level)
            logger.error(f"Level '{level}' is MISSING (0 samples).")
        elif ratio < MIN_LEVEL_RATIO:
            under_represented_levels.append((level, ratio, count))
            logger.warning(f"Level '{level}' is UNDER-REPRESENTED: {ratio:.2%} ({count} samples). Threshold: {MIN_LEVEL_RATIO:.0%}")
        else:
            logger.info(f"Level '{level}' OK: {ratio:.2%} ({count} samples).")

    # Determine failure
    if missing_levels:
        logger.error(f"CRITICAL FAILURE: The following levels are missing: {missing_levels}")
        logger.error("This violates SC-004 (Multi-level coverage). Aborting pipeline.")
        raise SystemExit("FATAL: Missing quantization levels detected.")

    if under_represented_levels:
        details = ", ".join([f"{lvl} ({cnt:.0%})" for lvl, _, cnt in under_represented_levels])
        logger.error(f"CRITICAL FAILURE: The following levels are under-represented (<10%): {details}")
        logger.error("This violates SC-004 (Multi-level coverage). Aborting pipeline.")
        raise SystemExit("FATAL: Under-represented quantization levels detected.")

    logger.info("SUCCESS: All quantization levels are present and sufficiently represented.")
    return True, ratios

def main():
    """Main entry point for T015d."""
    logger = setup_logger()
    logger.info("Starting T015d: Validate Dataset Levels")

    try:
        df = load_dataset(INPUT_FILE_PATH, logger)
        is_valid, ratios = validate_levels(df, logger)
        
        if is_valid:
            logger.info("Validation passed. Dataset is ready for downstream tasks.")
            sys.exit(0)
    except FileNotFoundError as e:
        logger.critical(str(e))
        sys.exit(1)
    except SystemExit as e:
        # Re-raise SystemExit to ensure the script exits with the error code
        raise
    except Exception as e:
        logger.critical(f"Unexpected error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()