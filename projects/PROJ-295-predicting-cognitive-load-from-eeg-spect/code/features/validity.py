"""
Validity checks for EEG spectral features.

Implements:
- Flagging missing sensors per epoch
- Measuring power stability and non-zero nature across subjects
"""
import numpy as np
import pandas as pd
from typing import List, Optional, Dict, Any, Tuple
import hashlib
import json
import datetime
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
EPSILON = 1e-9
MISSING_THRESHOLD = 0.05  # 5% missing data threshold

def calculate_file_checksum(filepath: str) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_state_checksums(output_path: str, state_path: str = "state.yaml") -> None:
    """Update the state file with checksums of output artifacts."""
    import yaml
    
    if not os.path.exists(state_path):
        logger.warning(f"State file {state_path} not found. Creating new one.")
        state = {"artifacts": {}, "updated_at": datetime.datetime.now().isoformat()}
    else:
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f) or {"artifacts": {}, "updated_at": datetime.datetime.now().isoformat()}
    
    if os.path.exists(output_path):
        checksum = calculate_file_checksum(output_path)
        state["artifacts"][output_path] = {
            "checksum": checksum,
            "updated_at": datetime.datetime.now().isoformat()
        }
    
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)

def identify_missing_sensor_epochs(
    epochs_data: np.ndarray,
    mask: Optional[np.ndarray] = None,
    threshold: float = MISSING_THRESHOLD
) -> pd.DataFrame:
    """
    Identify epochs with > threshold missing sensor data.
    
    Args:
        epochs_data: Array of shape (n_epochs, n_channels, n_times)
        mask: Boolean array of shape (n_channels,) where True indicates missing sensor.
             If None, inf/nan values in epochs_data are used to detect missing sensors.
        threshold: Fraction of missing sensors to flag an epoch.
    
    Returns:
        DataFrame with columns: epoch_id, missing_ratio, is_flagged
    """
    n_epochs, n_channels, n_times = epochs_data.shape
    
    if mask is None:
        # Detect missing sensors from data (inf or nan)
        mask = np.any(np.logical_or(np.isnan(epochs_data), np.isinf(epochs_data)), axis=2).any(axis=1)
    
    # Calculate missing ratio per epoch
    missing_counts = np.sum(mask, axis=1)
    missing_ratios = missing_counts / n_channels
    
    df = pd.DataFrame({
        'epoch_id': range(n_epochs),
        'missing_ratio': missing_ratios,
        'is_flagged': missing_ratios > threshold
    })
    
    return df

def flag_missing_sensors(
    epochs_data: np.ndarray,
    channel_names: List[str],
    threshold: float = MISSING_THRESHOLD
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Flag epochs with excessive missing sensor data and identify consistently missing channels.
    
    Args:
        epochs_data: Array of shape (n_epochs, n_channels, n_times)
        channel_names: List of channel names corresponding to epochs_data channels
        threshold: Fraction of epochs a channel must be missing in to be flagged as consistently missing
    
    Returns:
        Tuple of (epoch_flags_df, consistently_missing_channels)
    """
    n_epochs, n_channels, n_times = epochs_data.shape
    
    # Create a mask for missing data (nan or inf)
    missing_mask = np.logical_or(np.isnan(epochs_data), np.isinf(epochs_data))
    
    # Per epoch: ratio of missing channels
    missing_per_epoch = np.mean(missing_mask, axis=2)
    epoch_flags = pd.DataFrame({
        'epoch_id': range(n_epochs),
        'missing_ratio': missing_per_epoch,
        'is_flagged': missing_per_epoch > threshold
    })
    
    # Per channel: ratio of epochs with missing data
    missing_per_channel = np.mean(missing_mask, axis=0)
    consistently_missing = [
        channel for i, channel in enumerate(channel_names)
        if missing_per_channel[i] > threshold
    ]
    
    logger.info(f"Flagged {epoch_flags['is_flagged'].sum()} epochs with > {threshold*100}% missing data")
    logger.info(f"Found {len(consistently_missing)} consistently missing channels: {consistently_missing}")
    
    return epoch_flags, consistently_missing

def measure_power_stability(
    features_df: pd.DataFrame,
    feature_columns: Optional[List[str]] = None,
    subject_column: str = 'subject_id'
) -> Dict[str, Any]:
    """
    Measure stability and non-zero nature of extracted power values across subjects.
    
    Args:
        features_df: DataFrame with extracted features
        feature_columns: List of feature column names to analyze. If None, uses all numeric columns.
        subject_column: Name of the subject identifier column
    
    Returns:
        Dictionary with stability metrics per feature
    """
    if feature_columns is None:
        # Select all numeric columns except subject_id
        feature_columns = features_df.select_dtypes(include=[np.number]).columns.tolist()
        if subject_column in feature_columns:
            feature_columns.remove(subject_column)
    
    stats = {}
    
    for col in feature_columns:
        if col not in features_df.columns:
            logger.warning(f"Feature column {col} not found in DataFrame")
            continue
        
        values = features_df[col].dropna()
        
        if len(values) == 0:
            stats[col] = {
                'n_samples': 0,
                'mean': np.nan,
                'std': np.nan,
                'min': np.nan,
                'max': np.nan,
                'is_non_zero': False,
                'stability_score': np.nan,
                'message': 'No valid data'
            }
            continue
        
        mean_val = values.mean()
        std_val = values.std()
        
        # Check if values are effectively non-zero
        is_non_zero = (values.abs() > EPSILON).all()
        
        # Stability score: 1 / (1 + CV) where CV is coefficient of variation
        cv = std_val / (abs(mean_val) + EPSILON) if abs(mean_val) > EPSILON else np.inf
        stability_score = 1.0 / (1.0 + cv) if cv != np.inf else 0.0
        
        stats[col] = {
            'n_samples': len(values),
            'mean': float(mean_val),
            'std': float(std_val),
            'min': float(values.min()),
            'max': float(values.max()),
            'is_non_zero': bool(is_non_zero),
            'stability_score': float(stability_score),
            'cv': float(cv) if cv != np.inf else float('inf')
        }
        
        if not is_non_zero:
            logger.warning(f"Feature {col} contains zero or near-zero values!")
        else:
            logger.info(f"Feature {col}: mean={mean_val:.6f}, std={std_val:.6f}, stability={stability_score:.4f}")
    
    return stats

def main():
    """
    Main function to run validity checks on extracted features.
    
    This function:
    1. Loads cleaned epochs and extracted features
    2. Flags epochs with missing sensor data
    3. Measures power stability across subjects
    4. Outputs results to data/processed/validity_report.json
    """
    logger.info("Starting validity checks...")
    
    # Paths
    processed_dir = "data/processed"
    features_path = os.path.join(processed_dir, "features.parquet")
    epochs_path = os.path.join(processed_dir, "clean_epochs.npz")
    output_path = os.path.join(processed_dir, "validity_report.json")
    
    # Load features
    if not os.path.exists(features_path):
        logger.error(f"Features file not found: {features_path}")
        sys.exit(1)
    
    features_df = pd.read_parquet(features_path)
    logger.info(f"Loaded features for {len(features_df)} epochs")
    
    # Load epochs data if available
    epoch_flags_df = None
    consistently_missing_channels = []
    
    if os.path.exists(epochs_path):
        try:
            epochs_data = np.load(epochs_path, allow_pickle=True)
            # Assume structure: {'data': (n_epochs, n_channels, n_times), 'ch_names': [...]}
            data_array = epochs_data['data']
            ch_names = epochs_data['ch_names'].tolist() if 'ch_names' in epochs_data.files else None
            
            if ch_names is None:
                logger.warning("Channel names not found in epochs file, using generic names")
                ch_names = [f'ch_{i}' for i in range(data_array.shape[1])]
            
            epoch_flags_df, consistently_missing_channels = flag_missing_sensors(
                data_array, ch_names, threshold=MISSING_THRESHOLD
            )
        except Exception as e:
            logger.error(f"Failed to load epochs data: {e}")
    else:
        logger.warning(f"Epochs file not found: {epochs_path}, skipping sensor flagging")
    
    # Measure power stability
    stability_stats = measure_power_stability(features_df)
    
    # Compile report
    report = {
        'timestamp': datetime.datetime.now().isoformat(),
        'epoch_flags': {
            'total_epochs': len(features_df),
            'flagged_epochs': int(epoch_flags_df['is_flagged'].sum()) if epoch_flags_df is not None else 0,
            'flagged_ratio': float(epoch_flags_df['is_flagged'].mean()) if epoch_flags_df is not None else 0.0,
            'threshold': MISSING_THRESHOLD
        } if epoch_flags_df is not None else None,
        'consistently_missing_channels': consistently_missing_channels,
        'feature_stability': stability_stats
    }
    
    # Save report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    logger.info(f"Validity report saved to {output_path}")
    
    # Update state
    update_state_checksums(output_path)
    
    # Print summary
    print("\n=== Validity Check Summary ===")
    if report['epoch_flags']:
        print(f"Flagged epochs: {report['epoch_flags']['flagged_epochs']} / {report['epoch_flags']['total_epochs']} "
              f"({report['epoch_flags']['flagged_ratio']*100:.1f}%)")
    if report['consistently_missing_channels']:
        print(f"Consistently missing channels: {report['consistently_missing_channels']}")
    print("\nFeature stability:")
    for feat, stats in stability_stats.items():
        status = "✓" if stats['is_non_zero'] else "✗"
        print(f"  {status} {feat}: mean={stats['mean']:.6f}, stability={stats['stability_score']:.4f}")
    
    return report

if __name__ == "__main__":
    main()