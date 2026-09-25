"""
T024: Dimensional Fidelity Loss (Same-Dimension)

Computes the Mean Absolute Error (MAE) between the student scalar output and the
human annotation corresponding to the same primary dimension for each sample.

Excludes samples with missing primary_dimension, missing student_scalar, or 
missing human annotation for the target dimension.

Outputs:
  - data/processed/cleaned_data.parquet: Input data with new 'fidelity_loss' column
  - data/processed/fidelity_loss_summary.json: Statistics (mean, median, count, excluded_count)
  - data/processed/exclusions_log.json: Log of excluded samples
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Setup logging and directories (imported from alignment.py surface if needed, 
# but implementing inline to ensure self-containment and strict adherence to task)
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger(__name__)

def setup_directories():
    """Ensure required output directories exist."""
    data_processed = Path("data/processed")
    data_processed.mkdir(parents=True, exist_ok=True)
    return data_processed

def load_raw_data(input_path: Path, logger: logging.Logger) -> pd.DataFrame:
    """Load the aligned raw data from parquet."""
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading raw data from {input_path}")
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} samples")
    return df

def calculate_fidelity_loss(df: pd.DataFrame, logger: logging.Logger) -> tuple[pd.DataFrame, list[dict], dict]:
    """
    Calculate fidelity loss for each sample.
    
    Returns:
      - cleaned_df: DataFrame with 'fidelity_loss' column (NaN for excluded)
      - exclusions: List of dicts describing excluded samples
      - summary_stats: Dict with count, excluded_count (raw counts before filtering)
    """
    logger.info("Calculating dimensional fidelity loss...")
    
    # Identify columns
    required_cols = ['student_scalar', 'human_annotations', 'primary_dimension']
    for col in required_cols:
        if col not in df.columns:
            logger.error(f"Missing required column: {col}")
            raise ValueError(f"Missing required column: {col}")
    
    # Initialize exclusions list
    exclusions = []
    
    # Create a copy to avoid modifying original
    cleaned_df = df.copy()
    cleaned_df['fidelity_loss'] = np.nan
    
    valid_count = 0
    excluded_count = 0
    
    for idx, row in cleaned_df.iterrows():
        sample_id = row.get('sample_id', idx)
        
        # Check for missing primary_dimension
        if pd.isna(row['primary_dimension']) or not isinstance(row['primary_dimension'], (int, np.integer)):
            exclusions.append({
                "sample_id": sample_id,
                "reason": "missing_or_invalid_primary_dimension",
                "primary_dimension": row['primary_dimension']
            })
            excluded_count += 1
            continue
        
        target_dim = int(row['primary_dimension'])
        
        # Validate target dimension index (0-3)
        if target_dim < 0 or target_dim >= 4:
            exclusions.append({
                "sample_id": sample_id,
                "reason": "primary_dimension_out_of_bounds",
                "primary_dimension": target_dim
            })
            excluded_count += 1
            continue
        
        # Check for missing student_scalar
        if pd.isna(row['student_scalar']):
            exclusions.append({
                "sample_id": sample_id,
                "reason": "missing_student_scalar",
                "student_scalar": row['student_scalar']
            })
            excluded_count += 1
            continue
        
        # Check for missing human_annotations or missing value at target dimension
        human_annotations = row['human_annotations']
        if pd.isna(human_annotations):
            exclusions.append({
                "sample_id": sample_id,
                "reason": "missing_human_annotations",
                "target_dimension": target_dim
            })
            excluded_count += 1
            continue
        
        # Ensure human_annotations is a list/array with at least 4 elements
        if not isinstance(human_annotations, (list, np.ndarray)) or len(human_annotations) < 4:
            exclusions.append({
                "sample_id": sample_id,
                "reason": "human_annotations_format_invalid",
                "target_dimension": target_dim,
                "annotations_length": len(human_annotations) if isinstance(human_annotations, (list, np.ndarray)) else 0
            })
            excluded_count += 1
            continue
        
        target_annotation = human_annotations[target_dim]
        
        if pd.isna(target_annotation):
            exclusions.append({
                "sample_id": sample_id,
                "reason": "missing_annotation_for_target_dimension",
                "target_dimension": target_dim
            })
            excluded_count += 1
            continue
        
        # Calculate MAE (Absolute Error for single point)
        error = abs(float(row['student_scalar']) - float(target_annotation))
        cleaned_df.at[idx, 'fidelity_loss'] = error
        valid_count += 1
    
    # Calculate summary statistics
    valid_losses = cleaned_df['fidelity_loss'].dropna()
    summary_stats = {
        "count": int(len(valid_losses)),
        "excluded_count": excluded_count,
        "mean": float(valid_losses.mean()) if len(valid_losses) > 0 else None,
        "median": float(valid_losses.median()) if len(valid_losses) > 0 else None,
        "std": float(valid_losses.std()) if len(valid_losses) > 0 else None,
        "min": float(valid_losses.min()) if len(valid_losses) > 0 else None,
        "max": float(valid_losses.max()) if len(valid_losses) > 0 else None
    }
    
    logger.info(f"Processed {valid_count} valid samples, excluded {excluded_count} samples")
    return cleaned_df, exclusions, summary_stats

def save_cleaned_data(df: pd.DataFrame, output_path: Path, logger: logging.Logger):
    """Save the cleaned dataframe with fidelity_loss column."""
    logger.info(f"Saving cleaned data to {output_path}")
    df.to_parquet(output_path, index=False)
    logger.info("Saved successfully")

def save_summary(summary_stats: dict, output_path: Path, logger: logging.Logger):
    """Save summary statistics to JSON."""
    logger.info(f"Saving summary stats to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(summary_stats, f, indent=2)
    logger.info("Saved successfully")

def save_exclusions_log(exclusions: list[dict], output_path: Path, logger: logging.Logger):
    """Save exclusions log to JSON."""
    logger.info(f"Saving exclusions log to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(exclusions, f, indent=2)
    logger.info("Saved successfully")

def parse_args():
    parser = argparse.ArgumentParser(description="Calculate Dimensional Fidelity Loss")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/processed/raw_data.parquet",
        help="Path to input raw_data.parquet"
    )
    parser.add_argument(
        "--output-cleaned",
        type=str,
        default="data/processed/cleaned_data.parquet",
        help="Path to output cleaned_data.parquet"
    )
    parser.add_argument(
        "--output-summary",
        type=str,
        default="data/processed/fidelity_loss_summary.json",
        help="Path to output fidelity_loss_summary.json"
    )
    parser.add_argument(
        "--output-exclusions",
        type=str,
        default="data/processed/exclusions_log.json",
        help="Path to output exclusions_log.json"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    logger = setup_logging()
    setup_directories()
    
    input_path = Path(args.input)
    output_cleaned = Path(args.output_cleaned)
    output_summary = Path(args.output_summary)
    output_exclusions = Path(args.output_exclusions)
    
    try:
        # Load data
        df = load_raw_data(input_path, logger)
        
        # Calculate fidelity loss
        cleaned_df, exclusions, summary_stats = calculate_fidelity_loss(df, logger)
        
        # Save outputs
        save_cleaned_data(cleaned_df, output_cleaned, logger)
        save_summary(summary_stats, output_summary, logger)
        save_exclusions_log(exclusions, output_exclusions, logger)
        
        logger.info("T024 completed successfully")
        
    except Exception as e:
        logger.error(f"Error during T024 execution: {e}")
        raise

if __name__ == "__main__":
    main()
