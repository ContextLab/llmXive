import os
import sys
import json
import logging
import math
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.cluster import KMeans

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/resampling.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_processed_data(data_path: str) -> pd.DataFrame:
    """Load processed data with descriptors and targets."""
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Processed data not found at {data_path}")
    
    # Try parquet first, then CSV
    if path.suffix == '.parquet':
        return pd.read_parquet(path)
    elif path.suffix == '.csv':
        return pd.read_csv(path)
    else:
        # Default to parquet if extension is missing
        if path.with_suffix('.parquet').exists():
            return pd.read_parquet(path.with_suffix('.parquet'))
        raise ValueError(f"Unsupported file format: {path.suffix}")

def calculate_cv(values: np.ndarray, n_bins: int = 10) -> float:
    """
    Calculate Coefficient of Variation (CV) for a set of values.
    CV = std / mean
    Returns 0.0 if mean is zero to avoid division by zero.
    """
    if len(values) == 0:
        return 0.0
    
    mean_val = np.mean(values)
    if abs(mean_val) < 1e-10:
        return 0.0
    
    std_val = np.std(values)
    return std_val / abs(mean_val)

def dynamic_binning_resample(
    df: pd.DataFrame,
    target_col: str,
    feature_cols: List[str],
    n_bins: int = 10,
    min_samples_per_bin: int = 10,
    random_state: int = 42
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Perform dynamic binning resampling to balance the target distribution.
    
    Strategy:
    1. Bin the target variable into n_bins equal-frequency bins.
    2. Identify the minority class (smallest bin).
    3. Oversample minority bins (with replacement) and undersample majority bins.
    4. Ensure real-data CV <= 0.10 after resampling.
    
    Returns:
        Tuple of (resampled_df, metrics_dict)
    """
    logger.info(f"Starting dynamic binning resampling for {target_col}")
    
    # Create bins based on target distribution
    df = df.copy()
    
    # Calculate bin edges using quantiles for equal-frequency bins
    try:
        bin_edges = np.percentile(df[target_col], np.linspace(0, 100, n_bins + 1))
        # Ensure unique edges
        bin_edges = np.unique(bin_edges)
        if len(bin_edges) < 2:
            # If all values are the same, return original data
            logger.warning("All target values are identical. Returning original data.")
            return df, {"cv_real": 0.0, "cv_combined": 0.0}
        
        # Create bin labels
        df['_bin'] = pd.cut(df[target_col], bins=bin_edges, labels=False, include_lowest=True)
    except Exception as e:
        logger.error(f"Failed to create bins: {e}")
        raise
    
    # Calculate bin sizes
    bin_sizes = df['_bin'].value_counts().sort_index()
    min_bin_size = bin_sizes.min()
    max_bin_size = bin_sizes.max()
    
    # If bins are already balanced (ratio < 2), return original
    if max_bin_size / max(min_bin_size, 1) < 2.0:
        logger.info("Data is already balanced. Returning original data.")
        cv_real = calculate_cv(df[target_col].values)
        return df, {"cv_real": cv_real, "cv_combined": cv_real}
    
    # Target size for each bin (use the median bin size as target)
    target_size = bin_sizes.median()
    
    resampled_dfs = []
    
    for bin_id in sorted(df['_bin'].unique()):
        bin_data = df[df['_bin'] == bin_id]
        current_size = len(bin_data)
        
        if current_size < min_samples_per_bin:
            # Drop bins with too few samples
            logger.warning(f"Dropping bin {bin_id} with only {current_size} samples")
            continue
        
        if current_size < target_size:
            # Oversample (with replacement)
            n_samples_needed = int(target_size)
            bin_resampled = bin_data.sample(
                n=n_samples_needed,
                replace=True,
                random_state=random_state
            )
        else:
            # Undersample
            n_samples_needed = int(target_size)
            bin_resampled = bin_data.sample(
                n=n_samples_needed,
                replace=False,
                random_state=random_state
            )
        
        resampled_dfs.append(bin_resampled)
    
    if not resampled_dfs:
        raise ValueError("No bins remained after resampling")
    
    resampled_df = pd.concat(resampled_dfs, ignore_index=True)
    resampled_df = resampled_df.drop(columns=['_bin'])
    
    # Calculate CV for real data (original)
    cv_real = calculate_cv(df[target_col].values)
    # Calculate CV for combined (resampled) data
    cv_combined = calculate_cv(resampled_df[target_col].values)
    
    metrics = {
        "cv_real": cv_real,
        "cv_combined": cv_combined,
        "original_size": len(df),
        "resampled_size": len(resampled_df),
        "bins_used": len(resampled_dfs)
    }
    
    logger.info(f"Dynamic binning resampling complete. CV real: {cv_real:.4f}, CV combined: {cv_combined:.4f}")
    
    return resampled_df, metrics

def fallback_resample(
    df: pd.DataFrame,
    target_col: str,
    feature_cols: List[str],
    max_data_loss_pct: float = 0.20,
    random_state: int = 42
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Fallback resampling using cost-sensitive learning approach (class weights).
    
    This function simulates the effect of cost-sensitive learning by:
    1. Binning the target
    2. Assigning higher weights to minority bins
    3. Sampling based on these weights to create a balanced dataset
    
    Enforces combined CV <= 0.30 while keeping real-data CV <= 0.10.
    """
    logger.info(f"Starting fallback resampling for {target_col}")
    
    df = df.copy()
    
    # Create bins
    n_bins = 10
    try:
        bin_edges = np.percentile(df[target_col], np.linspace(0, 100, n_bins + 1))
        bin_edges = np.unique(bin_edges)
        if len(bin_edges) < 2:
            return df, {"cv_real": 0.0, "cv_combined": 0.0}
        
        df['_bin'] = pd.cut(df[target_col], bins=bin_edges, labels=False, include_lowest=True)
    except Exception as e:
        logger.error(f"Failed to create bins for fallback: {e}")
        raise
    
    # Calculate bin sizes and weights
    bin_sizes = df['_bin'].value_counts().sort_index()
    max_bin_size = bin_sizes.max()
    
    # Inverse frequency weighting
    bin_weights = max_bin_size / bin_sizes
    df['_weight'] = df['_bin'].map(bin_weights)
    
    # Calculate data loss
    original_size = len(df)
    
    # Sample with probability proportional to weights
    # Normalize weights to sum to 1
    weights = df['_weight'].values
    weights = weights / weights.sum()
    
    # Determine sample size to limit data loss
    max_loss = int(original_size * max_data_loss_pct)
    target_size = original_size - max_loss
    
    # Ensure we don't undersample too much
    target_size = max(target_size, int(original_size * 0.5))
    
    try:
        sampled_indices = np.random.choice(
            df.index,
            size=target_size,
            replace=False,
            p=weights
        )
        resampled_df = df.loc[sampled_indices].copy()
    except ValueError as e:
        # Fallback to simple random sampling if weights are invalid
        logger.warning(f"Weighted sampling failed: {e}. Using simple random sampling.")
        resampled_df = df.sample(n=target_size, replace=False, random_state=random_state)
    
    resampled_df = resampled_df.drop(columns=['_bin', '_weight'])
    
    # Calculate CVs
    cv_real = calculate_cv(df[target_col].values)
    cv_combined = calculate_cv(resampled_df[target_col].values)
    
    metrics = {
        "cv_real": cv_real,
        "cv_combined": cv_combined,
        "original_size": original_size,
        "resampled_size": len(resampled_df),
        "data_loss_pct": (original_size - len(resampled_df)) / original_size
    }
    
    logger.info(f"Fallback resampling complete. CV real: {cv_real:.4f}, CV combined: {cv_combined:.4f}")
    
    return resampled_df, metrics

def run_resampling_pipeline(
    input_path: str,
    output_path: str,
    target_col: str,
    feature_cols: List[str],
    cv_threshold_real: float = 0.10,
    cv_threshold_combined: float = 0.30,
    n_bins: int = 10,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Run the full resampling pipeline with CV constraint enforcement.
    
    This is the main entry point for T024. It:
    1. Loads processed data
    2. Attempts dynamic binning resampling
    3. Checks CV constraints
    4. Falls back to cost-sensitive approach if constraints are violated
    5. Returns the resampled data and metrics
    
    Constraints:
    - Real-data CV <= 0.10
    - Combined CV <= 0.30
    
    Returns:
        Dictionary with resampled data path and metrics
    """
    logger.info(f"Running resampling pipeline for {target_col}")
    logger.info(f"CV constraints: real <= {cv_threshold_real}, combined <= {cv_threshold_combined}")
    
    # Load data
    df = load_processed_data(input_path)
    logger.info(f"Loaded {len(df)} samples")
    
    # Ensure target column exists
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in data")
    
    # Step 1: Try dynamic binning resampling
    logger.info("Attempting dynamic binning resampling...")
    try:
        resampled_df, metrics = dynamic_binning_resample(
            df, target_col, feature_cols, n_bins=n_bins, random_state=random_state
        )
        
        cv_real = metrics["cv_real"]
        cv_combined = metrics["cv_combined"]
        
        logger.info(f"Dynamic binning results - CV real: {cv_real:.4f}, CV combined: {cv_combined:.4f}")
        
        # Check constraints
        if cv_real <= cv_threshold_real and cv_combined <= cv_threshold_combined:
            logger.info("CV constraints satisfied with dynamic binning.")
            success = True
        else:
            logger.warning(f"CV constraints not satisfied. Real: {cv_real:.4f} > {cv_threshold_real}, Combined: {cv_combined:.4f} > {cv_threshold_combined}")
            success = False
    except Exception as e:
        logger.error(f"Dynamic binning failed: {e}")
        success = False
    
    # Step 2: If constraints not met, try fallback
    if not success:
        logger.info("Attempting fallback resampling...")
        try:
            resampled_df, metrics = fallback_resample(
                df, target_col, feature_cols, random_state=random_state
            )
            
            cv_real = metrics["cv_real"]
            cv_combined = metrics["cv_combined"]
            
            logger.info(f"Fallback results - CV real: {cv_real:.4f}, CV combined: {cv_combined:.4f}")
            
            # Check constraints again
            if cv_real <= cv_threshold_real and cv_combined <= cv_threshold_combined:
                logger.info("CV constraints satisfied with fallback.")
                success = True
            else:
                logger.warning(f"CV constraints still not satisfied after fallback. Real: {cv_real:.4f}, Combined: {cv_combined:.4f}")
                # If still failing, we must raise an error as per T024 requirements
                raise ValueError(f"CV constraints cannot be met. Real CV: {cv_real:.4f}, Combined CV: {cv_combined:.4f}")
                
        except Exception as e:
            logger.error(f"Fallback resampling failed: {e}")
            raise RuntimeError(f"Resampling failed to meet CV constraints: {e}")
    
    # Save results
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save resampled data
    if output_path.endswith('.parquet'):
        resampled_df.to_parquet(output_path, index=False)
    else:
        resampled_df.to_csv(output_path, index=False)
    
    # Save metrics
    metrics_path = str(Path(output_path).with_suffix('.json'))
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Resampling pipeline complete. Output saved to {output_path}")
    logger.info(f"Metrics saved to {metrics_path}")
    
    return {
        "output_path": output_path,
        "metrics_path": metrics_path,
        "metrics": metrics,
        "success": success
    }

def main():
    """Main entry point for resampling pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run resampling pipeline with CV constraints')
    parser.add_argument('--input', type=str, required=True, help='Input data path')
    parser.add_argument('--output', type=str, required=True, help='Output data path')
    parser.add_argument('--target', type=str, required=True, help='Target column name')
    parser.add_argument('--features', type=str, nargs='+', required=True, help='Feature column names')
    parser.add_argument('--cv-real', type=float, default=0.10, help='Max CV for real data')
    parser.add_argument('--cv-combined', type=float, default=0.30, help='Max CV for combined data')
    parser.add_argument('--n-bins', type=int, default=10, help='Number of bins for dynamic binning')
    parser.add_argument('--random-state', type=int, default=42, help='Random state for reproducibility')
    
    args = parser.parse_args()
    
    try:
        result = run_resampling_pipeline(
            input_path=args.input,
            output_path=args.output,
            target_col=args.target,
            feature_cols=args.features,
            cv_threshold_real=args.cv_real,
            cv_threshold_combined=args.cv_combined,
            n_bins=args.n_bins,
            random_state=args.random_state
        )
        
        print(json.dumps(result, indent=2))
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == '__main__':
    main()