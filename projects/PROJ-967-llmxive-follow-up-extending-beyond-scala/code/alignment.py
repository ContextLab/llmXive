import argparse
import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('alignment.log')
        ]
    )
    return logging.getLogger(__name__)

def setup_directories(logger):
    dirs = [
        Path('data/raw'),
        Path('data/processed'),
        Path('results')
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory exists: {d}")

def load_raw_data(logger):
    """
    Loads the raw data from data/processed/raw_data.parquet.
    This file is produced by T012 (Ingestion).
    """
    input_path = Path('data/processed/raw_data.parquet')
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}. Please run T012 first.")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading raw data from {input_path}")
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} rows")
    return df

def align_and_filter_data(df, logger):
    """
    Verifies that teacher distributions, student scalars, and human annotations align by sample ID.
    Marks samples missing 'student_scalar' with 'excluded_reason: missing_student_scalar'.
    
    Returns:
        aligned_df: DataFrame with valid samples
        exclusions: List of dicts with sample_id and reason
    """
    required_cols = ['image_path', 'species_id', 'prompt_text', 'teacher_scores', 'student_scalar', 'human_annotations']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        raise ValueError(f"Missing required columns: {missing_cols}")

    exclusions = []
    aligned_df = df.copy()

    # Check for missing student_scalar (primary alignment requirement for this task)
    # The task specifically asks to mark samples missing student_scalar.
    # We assume 'student_scalar' might be null/NaN or missing entirely.
    
    initial_count = len(aligned_df)
    logger.info(f"Initial sample count: {initial_count}")

    # Identify rows where student_scalar is missing (NaN or None)
    mask_missing_scalar = aligned_df['student_scalar'].isna()
    
    if mask_missing_scalar.any():
        missing_indices = aligned_df[mask_missing_scalar].index
        logger.warning(f"Found {len(missing_indices)} samples with missing student_scalar.")
        
        for idx in missing_indices:
            sample_id = aligned_df.loc[idx, 'image_path'] # Using image_path as unique ID proxy if no explicit ID column
            exclusions.append({
                'sample_id': str(sample_id),
                'excluded_reason': 'missing_student_scalar'
            })
        
        # Filter out the missing ones
        aligned_df = aligned_df[~mask_missing_scalar].reset_index(drop=True)

    # Verify alignment of lists (teacher_scores and human_annotations should be lists of length 4)
    # This is a data integrity check. If they are not lists or wrong length, they are misaligned.
    def check_list_alignment(row):
        ts = row['teacher_scores']
        ha = row['human_annotations']
        
        if not isinstance(ts, (list, tuple)) or len(ts) != 4:
            return False
        if not isinstance(ha, (list, tuple)) or len(ha) != 4:
            return False
        return True

    # Note: Parquet might store lists as Python lists or numpy arrays.
    # We check length. If the column is object type containing lists, this works.
    # If it's a string representation, we might need to eval, but assuming proper parquet format.
    
    # Re-check length alignment after filtering scalar
    mask_misaligned = ~aligned_df.apply(check_list_alignment, axis=1)
    
    if mask_misaligned.any():
        misaligned_indices = aligned_df[mask_misaligned].index
        logger.warning(f"Found {len(misaligned_indices)} samples with misaligned teacher/human annotation lists.")
        
        for idx in misaligned_indices:
            sample_id = aligned_df.loc[idx, 'image_path']
            exclusions.append({
                'sample_id': str(sample_id),
                'excluded_reason': 'misaligned_annotation_lists'
            })
        
        aligned_df = aligned_df[~mask_misaligned].reset_index(drop=True)

    final_count = len(aligned_df)
    logger.info(f"Final aligned sample count: {final_count}")
    logger.info(f"Total excluded: {len(exclusions)}")

    return aligned_df, exclusions

def save_aligned_data(df, logger):
    """
    Saves the aligned and filtered data to data/processed/aligned_data.parquet.
    """
    output_path = Path('data/processed/aligned_data.parquet')
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved aligned data to {output_path}")
    return output_path

def save_exclusions_log(exclusions, logger):
    """
    Saves the exclusions log to data/processed/exclusions_log.json.
    """
    output_path = Path('data/processed/exclusions_log.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(exclusions, f, indent=2)
    logger.info(f"Saved exclusions log to {output_path}")
    return output_path

def parse_args():
    parser = argparse.ArgumentParser(description='Align and filter data for T013.')
    parser.add_argument('--input', type=str, default='data/processed/raw_data.parquet',
                        help='Path to input raw data file')
    parser.add_argument('--output', type=str, default='data/processed/aligned_data.parquet',
                        help='Path to output aligned data file')
    return parser.parse_args()

def main():
    logger = setup_logging()
    setup_directories(logger)
    
    try:
        df = load_raw_data(logger)
        aligned_df, exclusions = align_and_filter_data(df, logger)
        
        save_aligned_data(aligned_df, logger)
        save_exclusions_log(exclusions, logger)
        
        logger.info("Alignment task completed successfully.")
        
    except Exception as e:
        logger.error(f"Alignment task failed: {e}")
        raise

if __name__ == '__main__':
    main()
