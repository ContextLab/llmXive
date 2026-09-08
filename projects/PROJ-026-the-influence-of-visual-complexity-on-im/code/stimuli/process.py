import os
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import numpy as np

from .validate import validate_batch, get_invalid_images
from .metrics import calculate_edge_density, calculate_entropy, calculate_fractal_dim
from ..config import get_project_root, get_data_path

logger = logging.getLogger(__name__)

def categorize_complexity(df: pd.DataFrame, metric_col: str = 'edge_density') -> pd.DataFrame:
    """
    Categorize images into Low/High complexity based on the median of a given metric.
    
    Logic:
    - Calculate median of the specified metric column.
    - Map scores <= median to 'Low' and > median to 'High'.
    
    Args:
        df: DataFrame containing complexity metrics.
        metric_col: Column name to use for categorization.
        
    Returns:
        DataFrame with 'complexity_category' column added.
    """
    if metric_col not in df.columns:
        raise ValueError(f"Metric column '{metric_col}' not found in DataFrame.")
    
    # Filter out skipped/invalid rows for median calculation if necessary, 
    # though typically we categorize valid rows.
    valid_df = df[df['status'] == 'valid']
    
    if valid_df.empty:
        logger.warning("No valid images to categorize.")
        df['complexity_category'] = 'Unknown'
        return df

    median_score = valid_df[metric_col].median()
    
    def assign_category(score):
        if pd.isna(score):
            return 'Unknown'
        return 'Low' if score <= median_score else 'High'

    df['complexity_category'] = df[metric_col].apply(assign_category)
    
    # Log the threshold for reproducibility
    log_path = get_project_root() / 'logs' / 'categorization_threshold.log'
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'w') as f:
        f.write(f"Threshold Metric: {metric_col}\n")
        f.write(f"Median Threshold: {median_score}\n")
        f.write(f"Category Logic: <= {median_score} -> Low, > {median_score} -> High\n")
        
    logger.info(f"Categorization complete. Median threshold for {metric_col}: {median_score}")
    return df

def process_stimuli_batch(stimuli_dir: Optional[Path] = None) -> pd.DataFrame:
    """
    Iterate over images in stimuli_dir, compute metrics, and return a DataFrame.
    
    Action:
    - Validates images using T016 logic (validate_batch).
    - Computes metrics (edge_density, entropy, fractal_dim) for valid images.
    - Marks invalid images as 'skipped'.
    - Returns a DataFrame with columns: filename, edge_density, entropy, fractal_dim, status.
    
    Args:
        stimuli_dir: Path to directory containing stimulus images. Defaults to data/raw/stimuli.
        
    Returns:
        DataFrame with computed metrics and status.
    """
    if stimuli_dir is None:
        stimuli_dir = get_data_path() / 'raw' / 'stimuli'
        
    if not stimuli_dir.exists():
        raise FileNotFoundError(f"Stimuli directory not found: {stimuli_dir}")
        
    logger.info(f"Processing stimuli batch from: {stimuli_dir}")
    
    # 1. Validate images (T016)
    valid_images, invalid_images = validate_batch(stimuli_dir)
    invalid_filenames = {img.name for img in invalid_images}
    
    results = []
    
    # 2. Process valid images
    for img_path in valid_images:
        filename = img_path.name
        try:
            edge_density = calculate_edge_density(img_path)
            entropy_val = calculate_entropy(img_path)
            fractal_dim = calculate_fractal_dim(img_path)
            
            results.append({
                'filename': filename,
                'edge_density': edge_density,
                'entropy': entropy_val,
                'fractal_dim': fractal_dim,
                'status': 'valid'
            })
        except Exception as e:
            # If processing fails for a "valid" file, mark as skipped
            logger.error(f"Failed to process {filename}: {e}")
            results.append({
                'filename': filename,
                'edge_density': np.nan,
                'entropy': np.nan,
                'fractal_dim': np.nan,
                'status': 'skipped'
            })
    
    # 3. Add skipped images explicitly
    for invalid_path in invalid_images:
        results.append({
            'filename': invalid_path.name,
            'edge_density': np.nan,
            'entropy': np.nan,
            'fractal_dim': np.nan,
            'status': 'skipped'
        })
        
    df = pd.DataFrame(results)
    
    # Ensure columns are in the required order
    required_cols = ['filename', 'edge_density', 'entropy', 'fractal_dim', 'status']
    # Reorder if necessary, though append order should match
    if list(df.columns) != required_cols:
        df = df[required_cols]
        
    return df

def main():
    """
    Main entry point for batch processing.
    - Iterates data/raw/stimuli/
    - Computes metrics
    - Outputs data/processed/complexity_scores_raw.csv
    """
    setup_logger = logging.getLogger(__name__)
    setup_logger.info("Starting batch processing of stimuli.")
    
    # Load and process
    df = process_stimuli_batch()
    
    # Output path
    output_dir = get_data_path() / 'processed'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / 'complexity_scores_raw.csv'
    
    # Save
    df.to_csv(output_path, index=False)
    setup_logger.info(f"Saved raw complexity scores to {output_path}")
    setup_logger.info(f"Total images processed: {len(df)}")
    setup_logger.info(f"Valid: {len(df[df['status'] == 'valid'])}, Skipped: {len(df[df['status'] == 'skipped'])}")

if __name__ == "__main__":
    main()