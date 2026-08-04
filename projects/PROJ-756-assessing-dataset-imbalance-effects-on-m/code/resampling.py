import os
import sys
import json
import logging
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path('logs/resampling.log'))
    ]
)
logger = logging.getLogger(__name__)

# Constants
CV_THRESHOLD = 0.10
MAX_ITERATIONS = 50
MIN_SAMPLES_PER_BIN = 10
DATA_DIR = Path('data/processed')
RESULTS_DIR = Path('results')
BALANCED_DATA_DIR = Path('data/processed/balanced')

def calculate_cv(values: np.ndarray) -> float:
    """
    Calculate the Coefficient of Variation (CV) for a set of values.
    CV = (Standard Deviation / Mean)
    Returns 0.0 if mean is 0 to avoid division by zero.
    """
    if len(values) == 0:
        return 0.0
    mean = np.mean(values)
    if mean == 0:
        return 0.0
    std = np.std(values)
    return std / mean

def dynamic_binning_resample(
    df: pd.DataFrame,
    target_col: str,
    feature_cols: List[str],
    min_bins: int = 5,
    max_bins: int = 50,
    target_cv: float = CV_THRESHOLD
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Implement dynamic binning resampling with the constraint that the CV of
    bin counts must be <= target_cv (0.10) for the real data distribution.

    This function iteratively adjusts the number of bins to find a configuration
    where the CV of the resulting bin counts is <= 0.10.

    Args:
        df: Input DataFrame with target and feature columns
        target_col: Name of the target column
        feature_cols: List of feature column names
        min_bins: Minimum number of bins to try
        max_bins: Maximum number of bins to try
        target_cv: Target CV threshold (default 0.10)

    Returns:
        Tuple of (resampled DataFrame, metadata dictionary)
    """
    logger.info(f"Starting dynamic binning resampling for target '{target_col}'")
    logger.info(f"Initial data shape: {df.shape}")

    # Sort by target to create equal-frequency bins
    sorted_df = df.sort_values(by=target_col)

    best_df = None
    best_metadata = None
    best_cv = float('inf')

    # Try different numbers of bins to find one that satisfies CV <= 0.10
    for n_bins in range(min_bins, max_bins + 1):
        try:
            # Create equal-frequency bins
            # Use pd.qcut to create bins with approximately equal number of samples
            labels = pd.qcut(sorted_df[target_col], q=n_bins, duplicates='drop', retbins=False)
            
            # If qcut fails due to too many duplicates, skip this n_bins
            if len(labels.unique()) < n_bins:
                logger.debug(f"Skipping {n_bins} bins due to duplicate values in target")
                continue

            # Assign bin IDs
            sorted_df = sorted_df.copy()
            sorted_df['bin_id'] = pd.Categorical(labels).codes

            # Calculate bin counts
            bin_counts = sorted_df.groupby('bin_id').size().values

            # Check if any bin has fewer than MIN_SAMPLES_PER_BIN samples
            if np.any(bin_counts < MIN_SAMPLES_PER_BIN):
                logger.debug(f"Skipping {n_bins} bins due to small bin sizes")
                continue

            # Calculate CV of bin counts
            cv = calculate_cv(bin_counts)
            logger.debug(f"n_bins={n_bins}, CV={cv:.4f}, bin_counts range: [{bin_counts.min()}, {bin_counts.max()}]")

            # Check if we've found a configuration that satisfies the constraint
            if cv <= target_cv:
                # Upsample or downsample each bin to match the median bin size
                median_count = int(np.median(bin_counts))
                
                # Ensure median_count is at least MIN_SAMPLES_PER_BIN
                if median_count < MIN_SAMPLES_PER_BIN:
                    median_count = MIN_SAMPLES_PER_BIN

                resampled_bins = []
                for bin_id in sorted_df['bin_id'].unique():
                    bin_data = sorted_df[sorted_df['bin_id'] == bin_id]
                    current_count = len(bin_data)

                    if current_count < median_count:
                        # Upsample by random sampling with replacement
                        bin_resampled = bin_data.sample(
                            n=median_count, 
                            replace=True, 
                            random_state=42 + bin_id
                        )
                    elif current_count > median_count:
                        # Downsample by random sampling without replacement
                        bin_resampled = bin_data.sample(
                            n=median_count, 
                            replace=False, 
                            random_state=42 + bin_id
                        )
                    else:
                        bin_resampled = bin_data

                    resampled_bins.append(bin_resampled)

                resampled_df = pd.concat(resampled_bins, ignore_index=True)
                
                # Shuffle the resampled data
                resampled_df = resampled_df.sample(frac=1, random_state=42).reset_index(drop=True)

                # Remove the temporary bin_id column
                resampled_df = resampled_df.drop(columns=['bin_id'])

                # Calculate final CV of the resampled data
                final_bin_labels = pd.qcut(resampled_df[target_col], q=n_bins, duplicates='drop', retbins=False)
                final_counts = resampled_df.groupby(final_bin_labels).size().values
                final_cv = calculate_cv(final_counts)

                metadata = {
                    'target_col': target_col,
                    'n_bins': n_bins,
                    'original_cv': cv,
                    'final_cv': final_cv,
                    'target_cv': target_cv,
                    'median_bin_size': median_count,
                    'original_samples': len(df),
                    'resampled_samples': len(resampled_df),
                    'constraint_satisfied': final_cv <= target_cv,
                    'bin_counts_original': bin_counts.tolist(),
                    'bin_counts_resampled': final_counts.tolist()
                }

                logger.info(f"Found valid configuration: n_bins={n_bins}, final_cv={final_cv:.4f}")
                
                # Since we found a valid configuration, we can return immediately
                # Or we could continue to find the best one (lowest CV)
                # For now, return the first valid one
                return resampled_df, metadata

        except Exception as e:
            logger.debug(f"Error with {n_bins} bins: {str(e)}")
            continue

    # If no configuration satisfies the constraint, return the best one found
    if best_df is not None:
        logger.warning(f"No configuration satisfied CV <= {target_cv}. Returning best found with CV={best_cv:.4f}")
        return best_df, best_metadata
    
    # If we couldn't find any valid configuration, raise an error
    raise ValueError(
        f"Could not find a binning configuration with CV <= {target_cv}. "
        f"Try adjusting min_bins, max_bins, or target_cv."
    )

def fallback_resample(
    df: pd.DataFrame,
    target_col: str,
    feature_cols: List[str],
    method: str = 'smote'
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Fallback resampling method if dynamic binning fails.
    
    Args:
        df: Input DataFrame
        target_col: Target column name
        feature_cols: Feature column names
        method: Resampling method ('smote', 'class_weights', etc.)
    
    Returns:
        Tuple of (resampled DataFrame, metadata dictionary)
    """
    logger.warning(f"Fallback resampling triggered with method: {method}")
    
    # For now, just return the original data with a warning
    # In a full implementation, this would use SMOTE or class weights
    metadata = {
        'method': method,
        'original_samples': len(df),
        'resampled_samples': len(df),
        'note': 'Fallback used - data not resampled'
    }
    
    return df, metadata

def run_resampling_pipeline(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    target_col: Optional[str] = None,
    feature_cols: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Run the full resampling pipeline on processed data.
    
    Args:
        input_path: Path to input processed data CSV
        output_path: Path to save resampled data
        target_col: Target column name (if None, inferred from data)
        feature_cols: Feature column names (if None, inferred from data)
    
    Returns:
        Metadata dictionary about the resampling process
    """
    logger.info("Starting resampling pipeline")
    
    # Load data if path provided
    if input_path and input_path.exists():
        df = pd.read_csv(input_path)
    else:
        # Try to load from default location
        default_input = DATA_DIR / 'processed_data.csv'
        if default_input.exists():
            df = pd.read_csv(default_input)
        else:
            raise FileNotFoundError(f"No input data found at {input_path} or {default_input}")
    
    logger.info(f"Loaded data with shape: {df.shape}")
    
    # Infer target and features if not provided
    if target_col is None:
        # Look for common target column names
        possible_targets = ['formation_energy', 'energy_above_hull', 'band_gap']
        for t in possible_targets:
            if t in df.columns:
                target_col = t
                break
        if target_col is None:
            # Use the first numeric column that's not an ID
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            target_col = numeric_cols[0] if len(numeric_cols) > 0 else df.columns[0]
    
    if feature_cols is None:
        # Use all numeric columns except target
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        feature_cols = [c for c in numeric_cols if c != target_col]
    
    logger.info(f"Using target: {target_col}, features: {len(feature_cols)} columns")
    
    # Run dynamic binning resampling
    try:
        resampled_df, metadata = dynamic_binning_resample(
            df=df,
            target_col=target_col,
            feature_cols=feature_cols
        )
    except ValueError as e:
        logger.error(f"Dynamic binning failed: {str(e)}")
        # Try fallback
        resampled_df, metadata = fallback_resample(
            df=df,
            target_col=target_col,
            feature_cols=feature_cols
        )
    
    # Save resampled data if output path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        resampled_df.to_csv(output_path, index=False)
        logger.info(f"Saved resampled data to {output_path}")
    
    # Save metadata
    metadata_path = output_path.parent / f"{output_path.stem}_metadata.json" if output_path else RESULTS_DIR / 'resampling_metadata.json'
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Resampling complete. Final shape: {resampled_df.shape}")
    return metadata

def main():
    """Main entry point for resampling script."""
    logger.info("Resampling module main() called")
    
    # Example usage - in production, these would come from config or CLI args
    input_file = DATA_DIR / 'processed_data.csv'
    output_file = BALANCED_DATA_DIR / 'balanced_data.csv'
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.info("Please run descriptors.py first to generate processed data")
        return
    
    try:
        metadata = run_resampling_pipeline(
            input_path=input_file,
            output_path=output_file
        )
        print(json.dumps(metadata, indent=2))
    except Exception as e:
        logger.error(f"Resampling pipeline failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()