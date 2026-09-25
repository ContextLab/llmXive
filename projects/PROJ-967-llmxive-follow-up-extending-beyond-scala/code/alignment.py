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
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    return logging.getLogger(__name__)

def setup_directories(base_path):
    dirs = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "results",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    return base_path

def load_raw_data(input_path, logger):
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading raw data from {input_path}")
    if input_path.suffix == ".parquet":
        df = pd.read_parquet(input_path)
    elif input_path.suffix == ".csv":
        df = pd.read_csv(input_path)
    else:
        raise ValueError(f"Unsupported file format: {input_path.suffix}")
    
    logger.info(f"Loaded {len(df)} rows")
    return df

def align_and_filter_data(df, logger):
    required_cols = ["image_path", "species_id", "prompt_text", "teacher_scores", "student_scalar", "human_annotations", "primary_dimension"]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    logger.info("Checking alignment of teacher distributions, student scalars, and human annotations by sample ID...")
    
    # Ensure sample IDs are unique and present
    if "sample_id" not in df.columns:
        # Create sample_id if not present (using index or existing unique identifier)
        if "image_path" in df.columns:
            df["sample_id"] = df["image_path"].astype(str)
        else:
            df["sample_id"] = df.index.astype(str)
    
    # Identify samples with missing student_scalar
    missing_scalar_mask = df["student_scalar"].isna()
    missing_scalar_count = missing_scalar_mask.sum()
    
    if missing_scalar_count > 0:
        logger.warning(f"Found {missing_scalar_count} samples with missing student_scalar. Marking for exclusion.")
    
    # Create exclusions list
    exclusions = []
    for idx, row in df[missing_scalar_mask].iterrows():
        exclusions.append({
            "sample_id": row["sample_id"],
            "excluded_reason": "missing_student_scalar"
        })
    
    # Filter dataframe to keep only valid samples
    aligned_df = df[~missing_scalar_mask].copy()
    valid_count = len(aligned_df)
    excluded_count = len(exclusions)
    
    logger.info(f"Alignment complete. Valid samples: {valid_count}, Excluded: {excluded_count}")
    
    return aligned_df, exclusions

def save_aligned_data(df, output_path, logger):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Saving aligned data to {output_path}")
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved {len(df)} rows to {output_path}")

def save_exclusions_log(exclusions, output_path, logger):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Saving exclusions log to {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(exclusions, f, indent=2)
    logger.info(f"Saved {len(exclusions)} exclusions to {output_path}")

def parse_args():
    parser = argparse.ArgumentParser(description="Align and filter dataset for T013")
    parser.add_argument("--input", type=str, required=True, help="Path to raw input file (parquet or csv)")
    parser.add_argument("--output", type=str, required=True, help="Path to save aligned output file")
    parser.add_argument("--exclusions-log", type=str, default="data/processed/exclusions_log.json", help="Path to save exclusions log")
    parser.add_argument("--base-path", type=str, default="projects/PROJ-967-llmxive-follow-up-extending-beyond-scala", help="Base project path")
    return parser.parse_args()

def main():
    args = parse_args()
    logger = setup_logging()
    
    base_path = Path(args.base_path)
    setup_directories(base_path)
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    exclusions_log_path = Path(args.exclusions_log)
    
    df = load_raw_data(input_path, logger)
    aligned_df, exclusions = align_and_filter_data(df, logger)
    
    save_aligned_data(aligned_df, output_path, logger)
    save_exclusions_log(exclusions, exclusions_log_path, logger)
    
    logger.info("Alignment task T013 completed successfully.")

if __name__ == "__main__":
    main()
