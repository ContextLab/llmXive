import numpy as np
import pandas as pd
from typing import List, Optional

def identify_missing_sensor_epochs(
    epochs_metadata: pd.DataFrame,
    missing_threshold: float = 0.05
) -> pd.DataFrame:
    """
    Identify epochs with > missing_threshold missing sensor data.
    
    Args:
        epochs_metadata: DataFrame with epoch information including missing sensor counts.
        missing_threshold: Threshold fraction of missing data (e.g., 0.05 for 5%).
        
    Returns:
        DataFrame with epochs flagged as having too much missing data.
    """
    if 'n_missing_sensors' not in epochs_metadata.columns or 'n_channels' not in epochs_metadata.columns:
        raise ValueError("epochs_metadata must contain 'n_missing_sensors' and 'n_channels' columns.")
    
    # Calculate missing fraction
    epochs_metadata = epochs_metadata.copy()
    epochs_metadata['missing_fraction'] = epochs_metadata['n_missing_sensors'] / epochs_metadata['n_channels']
    
    # Flag epochs exceeding threshold
    epochs_metadata['is_excluded'] = epochs_metadata['missing_fraction'] > missing_threshold
    
    return epochs_metadata

def flag_missing_sensors(
    epochs_metadata: pd.DataFrame
) -> pd.DataFrame:
    """
    Flag specific missing sensors for each epoch.
    
    Args:
        epochs_metadata: DataFrame with epoch information.
        
    Returns:
        DataFrame with additional columns for missing sensor flags.
    """
    # This is a simplified version; real implementation would have a list of missing sensors
    # For now, we just flag based on the count
    epochs_metadata = epochs_metadata.copy()
    epochs_metadata['has_missing_sensors'] = epochs_metadata['n_missing_sensors'] > 0
    return epochs_metadata

def measure_power_stability(
    features_df: pd.DataFrame,
    min_subjects: int = 2
) -> dict:
    """
    Measure and report the stability and non-zero nature of extracted power values.
    
    Args:
        features_df: DataFrame with extracted features.
        min_subjects: Minimum number of subjects required for stability check.
        
    Returns:
        Dictionary with stability metrics.
    """
    metrics = {
        'mean_power': {},
        'std_power': {},
        'non_zero_ratio': {},
        'stability_score': 0.0,
        'is_stable': False
    }
    
    # Check if we have enough data
    if 'subject_id' in features_df.columns:
        n_subjects = features_df['subject_id'].nunique()
    else:
        n_subjects = 1
    
    if n_subjects < min_subjects:
        metrics['warning'] = f"Only {n_subjects} subject(s) found, stability check may be unreliable."
        return metrics
    
    # Calculate metrics per band
    for col in ['theta_power', 'alpha_power']:
        if col in features_df.columns:
            metrics['mean_power'][col] = float(features_df[col].mean())
            metrics['std_power'][col] = float(features_df[col].std())
            metrics['non_zero_ratio'][col] = float((features_df[col] > 1e-9).mean())
    
    # Calculate overall stability score (inverse of coefficient of variation)
    if 'theta_power' in features_df.columns and 'alpha_power' in features_df.columns:
        cv_theta = features_df['theta_power'].std() / (features_df['theta_power'].mean() + 1e-9)
        cv_alpha = features_df['alpha_power'].std() / (features_df['alpha_power'].mean() + 1e-9)
        
        # Lower CV is more stable
        avg_cv = (cv_theta + cv_alpha) / 2
        metrics['stability_score'] = 1.0 / (avg_cv + 1e-9)
        metrics['is_stable'] = metrics['stability_score'] > 1.0  # Arbitrary threshold
    
    return metrics

if __name__ == "__main__":
    print("Validity module loaded successfully.")
