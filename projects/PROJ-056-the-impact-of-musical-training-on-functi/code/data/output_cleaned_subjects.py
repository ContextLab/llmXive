"""
Module to output cleaned subject data to CSV.
Implements T019: Output data/processed/subjects_cleaned.csv
"""
import os
import sys
import pandas as pd
import logging
from pathlib import Path
from typing import Optional

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from utils.logging import get_logger
from data.preprocess import preprocess_subjects
from data.download import load_data, DataAccessError

logger = get_logger(__name__)

REQUIRED_COLUMNS = [
    'subject_id', 'group', 'years_of_training', 'age', 
    'sex', 'motion_score', 'ses_score'
]

def write_cleaned_subjects(
    mode: str = 'verification',
    synthetic_count: int = 10,
    output_path: Optional[str] = None
) -> str:
    """
    Load data (synthetic or real), preprocess it, and write to CSV.
    
    Args:
        mode: 'verification' (uses synthetic data) or 'analysis' (requires real data)
        synthetic_count: Number of synthetic subjects to generate if mode='verification'
        output_path: Optional custom output path. Defaults to data/processed/subjects_cleaned.csv
    
    Returns:
        Path to the generated CSV file.
    
    Raises:
        DataAccessError: If real data is missing in analysis mode.
        ValueError: If data does not meet minimum requirements.
    """
    # Determine output path
    if output_path is None:
        output_path = str(Path("data/processed/subjects_cleaned.csv"))
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting subject cleaning pipeline. Mode: {mode}")
    
    # 1. Load Data
    try:
        if mode == 'verification':
            logger.info(f"Generating {synthetic_count} synthetic subjects for verification.")
            # Import here to avoid circular imports if necessary, though structure suggests top-level is fine
            from data.synthetic_generator import generate_synthetic_dataset
            df = generate_synthetic_dataset(n_subjects=synthetic_count)
        else:
            # Analysis mode: Try to load from default real data location or raise error
            # The download.py load_data function handles the logic of checking existence
            # and raising DataAccessError if real data is missing.
            logger.info("Attempting to load real data for analysis mode.")
            # Assuming a default path or environment variable, but T014 logic handles the error
            df = load_data(path="data/raw/real_subjects.csv", mode='analysis')
    except DataAccessError as e:
        logger.error(f"Data access failed: {e}")
        raise
    except FileNotFoundError:
        # Fallback for analysis mode if path not found but mode is analysis
        if mode == 'analysis':
            raise DataAccessError("Data Source Missing: Real data required for Analysis Mode")
        raise

    if df is None or df.empty:
        raise ValueError("Loaded data is empty.")

    # 2. Preprocess Data
    # T015: Filter by years_of_training >= 1
    # T016: Handle confounders (PSM or Regression)
    # T018: Error handling for corrupted NIfTI is handled in load_nifti_safe if applicable,
    #       but here we assume df is already clean or the preprocessing function handles row-wise errors.
    
    logger.info("Applying preprocessing filters and confounder handling.")
    df_clean = preprocess_subjects(df, mode=mode)

    # 3. Validate Output Columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df_clean.columns]
    if missing_cols:
        raise ValueError(f"Preprocessing failed to produce required columns: {missing_cols}")

    # 4. Select and Order Columns
    df_final = df_clean[REQUIRED_COLUMNS].copy()

    # 5. Write to CSV
    logger.info(f"Writing cleaned subjects to {output_file}")
    df_final.to_csv(output_file, index=False)

    logger.info(f"Successfully wrote {len(df_final)} subjects to {output_file}")
    return output_file

def main():
    """Entry point for running the output script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Output cleaned subject data to CSV.")
    parser.add_argument(
        '--mode', 
        choices=['verification', 'analysis'], 
        default='verification',
        help="Mode of operation. Verification uses synthetic data."
    )
    parser.add_argument(
        '--count', 
        type=int, 
        default=10,
        help="Number of synthetic subjects to generate (only used in verification mode)."
    )
    parser.add_argument(
        '--output', 
        type=str, 
        default=None,
        help="Output file path."
    )

    args = parser.parse_args()

    try:
        result_path = write_cleaned_subjects(
            mode=args.mode,
            synthetic_count=args.count,
            output_path=args.output
        )
        print(f"Output written to: {result_path}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
