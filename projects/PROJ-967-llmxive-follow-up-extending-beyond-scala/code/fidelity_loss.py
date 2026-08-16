import argparse
import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd
import numpy as np

# --- Logging Setup ---
def setup_logging():
    """Configure logging to stdout and file."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("results/fidelity_loss.log"),
        ],
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# --- Data Loading ---
def load_raw_data(input_path: str) -> pd.DataFrame:
    """
    Load the aligned raw dataset from parquet.
    Expects columns: prompt, image_url, teacher_scores, student_scalar,
                    human_annotations, primary_dimension, excluded_reason.
    """
    logger.info(f"Loading raw data from {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")
    return df

# --- Core Logic ---
def calculate_fidelity_loss(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Compute dimensional fidelity loss for valid samples.
    
    1. Exclude samples where:
       - primary_dimension is null/missing
       - student_scalar is missing
       - human_annotations for the primary dimension is missing
    2. Calculate MAE between student_scalar and the human score for the primary dimension.
    3. Return filtered dataframe and summary stats.
    """
    logger.info("Calculating dimensional fidelity loss...")
    
    # Make a copy to avoid modifying original
    data = df.copy()
    
    # Normalize column access helpers
    def get_annotation_score(row, dim):
        try:
            annotations = row.get('human_annotations')
            if pd.isna(annotations):
                return None
            if isinstance(annotations, dict):
                return annotations.get(dim)
            # Handle potential stringified dict or list if schema varies slightly
            return None
        except Exception:
            return None

    # Identify valid rows
    valid_indices = []
    excluded_reasons = []
    
    for idx, row in data.iterrows():
        reason = None
        
        # Check primary_dimension
        primary_dim = row.get('primary_dimension')
        if pd.isna(primary_dim) or primary_dim is None:
            reason = 'missing_primary_dimension'
        
        # Check student_scalar
        elif pd.isna(row.get('student_scalar')):
            reason = 'missing_student_scalar'
        
        # Check human annotation for primary dimension
        else:
            human_score = get_annotation_score(row, primary_dim)
            if human_score is None or pd.isna(human_score):
                reason = f'missing_human_annotation_{primary_dim}'
        
        if reason:
            excluded_reasons.append(reason)
        else:
            valid_indices.append(idx)
    
    # Filter dataframe
    valid_df = data.loc[valid_indices].copy()
    
    if len(valid_df) == 0:
        logger.warning("No valid samples found for fidelity loss calculation.")
        return valid_df, {
            "mean": None,
            "median": None,
            "count": 0,
            "excluded_count": len(data),
            "excluded_reasons": excluded_reasons
        }

    # Calculate Fidelity Loss (MAE per sample: |student - human|)
    def compute_loss(row):
        student = row['student_scalar']
        dim = row['primary_dimension']
        annotations = row['human_annotations']
        human = annotations.get(dim) if isinstance(annotations, dict) else None
        if human is None:
            return np.nan
        return abs(float(student) - float(human))

    valid_df['fidelity_loss'] = valid_df.apply(compute_loss, axis=1)
    
    # Calculate Summary Statistics
    loss_values = valid_df['fidelity_loss'].dropna()
    summary = {
        "mean": float(loss_values.mean()) if len(loss_values) > 0 else None,
        "median": float(loss_values.median()) if len(loss_values) > 0 else None,
        "count": int(len(valid_df)),
        "excluded_count": int(len(data) - len(valid_df)),
        "excluded_reasons": excluded_reasons
    }
    
    logger.info(f"Calculated fidelity loss for {len(valid_df)} samples. Mean: {summary['mean']:.4f}")
    return valid_df, summary

# --- Output ---
def save_cleaned_data(df: pd.DataFrame, output_path: str):
    """Save the filtered dataframe to parquet."""
    logger.info(f"Saving cleaned data to {output_path}")
    df.to_parquet(output_path, index=False)
    logger.info("Saved successfully.")

def save_summary(summary: dict, output_path: str):
    """Save summary statistics to JSON."""
    logger.info(f"Saving summary to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info("Saved successfully.")

# --- CLI ---
def parse_args():
    parser = argparse.ArgumentParser(description="Calculate Dimensional Fidelity Loss")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/processed/raw_data.parquet",
        help="Path to the aligned raw dataset (parquet)"
    )
    parser.add_argument(
        "--output-cleaned", 
        type=str, 
        default="data/processed/cleaned_data.parquet",
        help="Path to save the filtered dataset"
    )
    parser.add_argument(
        "--output-summary", 
        type=str, 
        default="data/processed/fidelity_loss_summary.json",
        help="Path to save the summary statistics"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    
    try:
        # 1. Load
        df = load_raw_data(args.input)
        
        # 2. Calculate
        cleaned_df, summary = calculate_fidelity_loss(df)
        
        # 3. Save
        save_cleaned_data(cleaned_df, args.output_cleaned)
        save_summary(summary, args.output_summary)
        
        logger.info("Fidelity loss calculation completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
