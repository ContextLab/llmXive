"""
Module to output the cleaned subjects dataset to CSV.

This module implements Task T019: Output `data/processed/subjects_cleaned.csv`
with the required columns after preprocessing.
"""
import os
import sys
import pandas as pd
import logging
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.logging import get_logger
from utils.memory_monitor import check_memory_limit, get_current_memory_mb
from data.preprocess import preprocess_subjects
from data.download import load_data

logger = get_logger(__name__)

REQUIRED_COLUMNS = [
    'subject_id',
    'group',
    'years_of_training',
    'age',
    'sex',
    'motion_score',
    'ses_score'
]

def write_cleaned_subjects(
    input_mode: str = 'verification',
    synthetic_seed: int = 42,
    output_path: Optional[str] = None
) -> str:
    """
    Preprocesses subjects and writes the cleaned dataset to a CSV file.

    This function:
    1. Loads data (synthetic for verification, raises error for analysis if missing).
    2. Runs the full preprocessing pipeline (filtering, confounder handling).
    3. Validates the output schema.
    4. Writes the result to `data/processed/subjects_cleaned.csv`.

    Args:
        input_mode: 'verification' or 'analysis'.
        synthetic_seed: Random seed for synthetic data generation.
        output_path: Optional custom output path. Defaults to project standard.

    Returns:
        The absolute path to the written CSV file.

    Raises:
        ValueError: If the output data is missing required columns.
        MemoryLimitExceeded: If memory usage exceeds the limit during processing.
    """
    check_memory_limit()

    # Determine output path
    if output_path is None:
        base_dir = Path(__file__).resolve().parent.parent.parent
        output_path = base_dir / "data" / "processed" / "subjects_cleaned.csv"
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading data in mode: {input_mode}")
    
    # Load data using the download module (T014)
    # Note: load_data expects a path, but for synthetic it ignores it or uses it as root.
    # We pass a dummy path for verification mode as per T014 logic.
    df = load_data(path="data/raw", mode=input_mode)

    logger.info(f"Loaded {len(df)} subjects before preprocessing.")

    # Run preprocessing pipeline (T015, T016, T018)
    # This returns a DataFrame with cleaned and matched data
    df_cleaned = preprocess_subjects(df)

    logger.info(f"Preprocessing complete. {len(df_cleaned)} subjects remaining.")

    # Validate output columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df_cleaned.columns]
    if missing_cols:
        raise ValueError(f"Output data missing required columns: {missing_cols}")

    # Ensure column order matches spec
    df_output = df_cleaned[REQUIRED_COLUMNS]

    # Check memory again before writing large file
    check_memory_limit()

    # Write to CSV
    logger.info(f"Writing cleaned subjects to {output_path}")
    df_output.to_csv(output_path, index=False)

    logger.info(f"Successfully wrote {len(df_output)} rows to {output_path}")
    
    # Verify file exists and is not empty
    if not output_path.exists():
        raise FileNotFoundError(f"Output file was not created: {output_path}")
    
    if output_path.stat().st_size == 0:
        raise ValueError(f"Output file is empty: {output_path}")

    return str(output_path)

def main():
    """Entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(description="Output cleaned subjects to CSV")
    parser.add_argument(
        "--mode", 
        choices=["verification", "analysis"], 
        default="verification",
        help="Run mode: verification (synthetic) or analysis (real data)"
    )
    parser.add_argument(
        "--seed", 
        type=int, 
        default=42,
        help="Random seed for synthetic data generation"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=None,
        help="Custom output path (optional)"
    )

    args = parser.parse_args()

    try:
        output_file = write_cleaned_subjects(
            input_mode=args.mode,
            synthetic_seed=args.seed,
            output_path=args.output
        )
        print(f"SUCCESS: Output written to {output_file}")
    except Exception as e:
        logger.error(f"Failed to write cleaned subjects: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()