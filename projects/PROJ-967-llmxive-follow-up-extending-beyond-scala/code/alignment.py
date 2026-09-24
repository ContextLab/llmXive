"""
Alignment Module (Task T013)

Verifies that teacher distributions, student scalars, and human annotations
align by sample ID. Marks samples missing `student_scalar` with
`excluded_reason: 'missing_student_scalar'`.

Reads from: data/processed/raw_data.parquet
Writes to: data/processed/aligned_data.parquet
           data/processed/exclusions_log.json
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd
import numpy as np

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    return logging.getLogger(__name__)

def setup_directories(base_path: Path):
    processed_dir = base_path / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    return processed_dir

def load_raw_data(input_path: Path, logger: logging.Logger) -> pd.DataFrame:
    if not input_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {input_path}")
    
    logger.info(f"Loading raw data from {input_path}")
    try:
        df = pd.read_parquet(input_path)
    except Exception as e:
        logger.error(f"Failed to load parquet file: {e}")
        raise
    
    required_cols = ["image_path", "species_id", "teacher_scores", "student_scalar", "human_annotations"]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in raw data: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} samples with columns: {list(df.columns)}")
    return df

def align_and_filter_data(df: pd.DataFrame, logger: logging.Logger) -> tuple[pd.DataFrame, list[dict]]:
    """
    Aligns data by verifying presence of required fields.
    Returns aligned dataframe and a list of exclusion records.
    """
    logger.info("Starting alignment verification...")
    
    exclusions = []
    valid_indices = []

    for idx, row in df.iterrows():
        is_valid = True
        reason = None

        # Check for student_scalar presence
        # student_scalar might be NaN or missing
        if pd.isna(row.get("student_scalar")):
            is_valid = False
            reason = "missing_student_scalar"
        
        # Check for teacher_scores presence (expecting a list/array of 4 floats)
        teacher_scores = row.get("teacher_scores")
        if pd.isna(teacher_scores) or (isinstance(teacher_scores, float) and np.isnan(teacher_scores)):
            if reason is None:
                is_valid = False
                reason = "missing_teacher_scores"
        
        # Check for human_annotations presence
        human_annotations = row.get("human_annotations")
        if pd.isna(human_annotations) or (isinstance(human_annotations, float) and np.isnan(human_annotations)):
            if reason is None:
                is_valid = False
                reason = "missing_human_annotations"

        if not is_valid:
            exclusions.append({
                "sample_id": row.get("image_path", f"idx_{idx}"),
                "excluded_reason": reason,
                "index": idx
            })
        else:
            valid_indices.append(idx)

    logger.info(f"Alignment complete. Total: {len(df)}, Valid: {len(valid_indices)}, Excluded: {len(exclusions)}")
    
    if len(valid_indices) > 0:
        aligned_df = df.iloc[valid_indices].reset_index(drop=True)
    else:
        aligned_df = pd.DataFrame(columns=df.columns)
        logger.warning("No valid samples found after alignment.")

    return aligned_df, exclusions

def save_aligned_data(df: pd.DataFrame, output_path: Path, logger: logging.Logger):
    logger.info(f"Saving aligned data to {output_path}")
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved {len(df)} rows to {output_path}")

def save_exclusions_log(exclusions: list[dict], output_path: Path, logger: logging.Logger):
    logger.info(f"Saving exclusions log to {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(exclusions, f, indent=2)
    logger.info(f"Saved {len(exclusions)} exclusion records")

def parse_args():
    parser = argparse.ArgumentParser(description="Align and filter dataset samples (T013)")
    parser.add_argument(
        "--input-path",
        type=str,
        default="data/processed/raw_data.parquet",
        help="Path to the raw data parquet file",
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="data/processed/aligned_data.parquet",
        help="Path to save the aligned data",
    )
    parser.add_argument(
        "--exclusions-path",
        type=str,
        default="data/processed/exclusions_log.json",
        help="Path to save the exclusions log",
    )
    return parser.parse_args()

def main():
    args = parse_args()
    logger = setup_logging()
    
    base_path = Path.cwd()
    # Ensure output directories exist
    setup_directories(base_path)

    input_path = base_path / args.input_path
    output_path = base_path / args.output_path
    exclusions_path = base_path / args.exclusions_path

    try:
        df = load_raw_data(input_path, logger)
        aligned_df, exclusions = align_and_filter_data(df, logger)
        
        save_aligned_data(aligned_df, output_path, logger)
        save_exclusions_log(exclusions, exclusions_path, logger)
        
        logger.info("Task T013 Alignment completed successfully.")
    except Exception as e:
        logger.error(f"Task T013 failed: {e}")
        raise

if __name__ == "__main__":
    main()
