import numpy as np
import pandas as pd
import os
import sys
import hashlib
import datetime
from typing import Dict, List, Optional, Tuple, Union
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
EPSILON = 1e-9
MIN_MISSING_THRESHOLD = 0.05  # 5%

def calculate_file_checksum(file_path: str, algorithm: str = 'sha256') -> str:
    """Calculate the checksum of a file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_func = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def update_state_checksums(output_path: str, state_file: str = 'state/pipeline_state.yaml'):
    """Update the pipeline state file with checksums and timestamp."""
    import yaml
    
    if not os.path.exists(state_file):
        logger.warning(f"State file not found at {state_file}. Creating new state file.")
        state = {
            'updated_at': datetime.datetime.now().isoformat(),
            'checksums': {}
        }
    else:
        with open(state_file, 'r') as f:
            state = yaml.safe_load(f)
        if state is None:
            state = {'updated_at': datetime.datetime.now().isoformat(), 'checksums': {}}
    
    state['updated_at'] = datetime.datetime.now().isoformat()
    
    if os.path.exists(output_path):
        checksum = calculate_file_checksum(output_path)
        state['checksums'][os.path.basename(output_path)] = checksum
        logger.info(f"Updated state with checksum for {output_path}: {checksum}")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    
    with open(state_file, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)

def compute_gaze_variance(gaze_data: pd.DataFrame, window_size: int = 1) -> pd.Series:
    """
    Compute gaze variance per epoch based on gaze data.
    
    Args:
        gaze_data: DataFrame with columns ['epoch_id', 'x', 'y'] or similar coordinates.
        window_size: Size of the rolling window for variance calculation (in samples).
        
    Returns:
        Series of variance values indexed by epoch_id.
    """
    if 'epoch_id' not in gaze_data.columns:
        raise ValueError("gaze_data must contain 'epoch_id' column")
    
    # Assuming 'x' and 'y' are the gaze coordinates
    if 'x' not in gaze_data.columns or 'y' not in gaze_data.columns:
        # Try to infer coordinate columns if not named x/y
        coord_cols = [c for c in gaze_data.columns if c.lower() in ['x', 'y', 'lon', 'lat', 'pos_x', 'pos_y']]
        if len(coord_cols) < 2:
            raise ValueError("gaze_data must contain at least two coordinate columns (e.g., 'x', 'y')")
        x_col, y_col = coord_cols[0], coord_cols[1]
    else:
        x_col, y_col = 'x', 'y'
    
    # Calculate Euclidean distance variance or separate variance?
    # Based on typical cognitive load metrics, we often look at variance in position over time.
    # Let's compute the variance of the magnitude of movement or simply the variance of x and y combined.
    # A common approach is variance of the distance from the mean or simply sum of variances.
    # Here we compute the variance of the Euclidean distance from the mean position for each epoch.
    
    def epoch_variance(group):
        if len(group) < 2:
            return np.nan
        x = group[x_col].values
        y = group[y_col].values
        # Variance of the magnitude of the gaze point relative to the epoch mean
        # Or simply the sum of variances of x and y
        return np.var(x) + np.var(y)
    
    variance_series = gaze_data.groupby('epoch_id').apply(epoch_variance)
    return variance_series

def generate_cognitive_load_labels(
    epochs_data: pd.DataFrame,
    gaze_data: pd.DataFrame,
    output_path: str
) -> pd.DataFrame:
    """
    Generate continuous cognitive load labels from gaze variance.
    
    Args:
        epochs_data: DataFrame containing epoch metadata (epoch_id, subject_id).
        gaze_data: DataFrame containing gaze coordinates per epoch.
        output_path: Path to save the generated labels.
        
    Returns:
        DataFrame with cognitive load labels.
    """
    logger.info(f"Generating cognitive load labels from {len(gaze_data)} gaze samples...")
    
    # Compute variance per epoch
    gaze_variance = compute_gaze_variance(gaze_data)
    
    # Merge with epochs data
    if 'epoch_id' not in epochs_data.columns:
        raise ValueError("epochs_data must contain 'epoch_id' column")
    
    labels_df = epochs_data[['epoch_id', 'subject_id']].copy()
    labels_df = labels_df.merge(gaze_variance.reset_index(), on='epoch_id', how='left')
    labels_df.rename(columns={0: 'gaze_variance'}, inplace=True)
    
    # Handle missing values (if any epoch has no gaze data)
    missing_count = labels_df['gaze_variance'].isna().sum()
    if missing_count > 0:
        logger.warning(f"{missing_count} epochs have missing gaze variance data. Filling with 0.")
        labels_df['gaze_variance'].fillna(0, inplace=True)
    
    # Save to disk
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    labels_df.to_csv(output_path, index=False)
    logger.info(f"Cognitive load labels saved to {output_path}")
    
    return labels_df

def normalize_labels(
    labels_df: pd.DataFrame,
    output_path: Optional[str] = None,
    per_subject: bool = True
) -> pd.DataFrame:
    """
    Normalize cognitive load labels via min-max scaling per subject.
    
    FR-004: Normalize labels via min-max scaling per subject.
    
    Args:
        labels_df: DataFrame with columns ['epoch_id', 'subject_id', 'gaze_variance'] (or similar label column).
        output_path: Optional path to save the normalized labels.
        per_subject: If True, normalize within each subject; if False, normalize globally.
        
    Returns:
        DataFrame with normalized labels.
    """
    logger.info("Normalizing cognitive load labels...")
    
    if 'subject_id' not in labels_df.columns:
        raise ValueError("labels_df must contain 'subject_id' column")
    
    # Identify the label column (assume it's the one that isn't epoch_id or subject_id)
    label_cols = [c for c in labels_df.columns if c not in ['epoch_id', 'subject_id']]
    if not label_cols:
        raise ValueError("No label column found in labels_df")
    
    # We expect 'gaze_variance' or similar as the primary label
    label_col = label_cols[0]
    
    normalized_df = labels_df.copy()
    
    def min_max_normalize(series: pd.Series) -> pd.Series:
        min_val = series.min()
        max_val = series.max()
        if max_val - min_val < EPSILON:
            # If all values are the same, return 0.5 (midpoint) or 0? 
            # Returning 0.5 indicates neutral load if no variation exists.
            return pd.Series([0.5] * len(series), index=series.index)
        return (series - min_val) / (max_val - min_val)
    
    if per_subject:
        if 'subject_id' not in normalized_df.columns:
            raise ValueError("per_subject=True requires 'subject_id' column")
        
        normalized_df['normalized_label'] = normalized_df.groupby('subject_id')[label_col].transform(min_max_normalize)
        logger.info("Normalized labels per subject.")
    else:
        normalized_df['normalized_label'] = min_max_normalize(normalized_df[label_col])
        logger.info("Normalized labels globally.")
    
    # Save if path provided
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        normalized_df.to_csv(output_path, index=False)
        logger.info(f"Normalized labels saved to {output_path}")
        
        # Update state
        update_state_checksums(output_path)
    
    return normalized_df

def main():
    """
    Main entry point for label generation and normalization.
    This script is designed to be run after T026 (generate_cognitive_load_labels).
    It assumes the output of T026 exists at a standard path or is passed via args.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Normalize cognitive load labels per subject.")
    parser.add_argument('--input-path', type=str, required=True, 
                        help='Path to the unnormalized labels CSV (output of T026).')
    parser.add_argument('--output-path', type=str, required=True,
                        help='Path to save the normalized labels CSV.')
    parser.add_argument('--per-subject', action='store_true', default=True,
                        help='Normalize per subject (default: True).')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_path):
        raise FileNotFoundError(f"Input file not found: {args.input_path}")
    
    logger.info(f"Loading labels from {args.input_path}")
    labels_df = pd.read_csv(args.input_path)
    
    logger.info(f"Input shape: {labels_df.shape}")
    logger.info(f"Columns: {list(labels_df.columns)}")
    
    # Normalize
    normalized_df = normalize_labels(
        labels_df, 
        output_path=args.output_path, 
        per_subject=args.per_subject
    )
    
    logger.info(f"Normalization complete. Output shape: {normalized_df.shape}")
    logger.info(f"Sample normalized labels:\n{normalized_df.head()}")
    
    return normalized_df

if __name__ == "__main__":
    main()