import numpy as np
import pandas as pd
from typing import List, Optional
import hashlib
import json
import datetime
import os
import sys

# Import from sibling modules if needed, though this task focuses on internal logic
# We assume the caller provides the dataframe.

def identify_missing_sensor_epochs(
    epochs_metadata: pd.DataFrame,
    missing_threshold: float = 0.05
) -> pd.DataFrame:
    """
    Identify epochs with > missing_threshold missing sensor data and EXCLUDE them.
    
    This function implements FR-003: Exclude epochs with > 5% missing sensor data.
    
    Args:
        epochs_metadata: DataFrame with epoch information including missing sensor counts.
                         Expected columns: 'n_missing_sensors', 'n_channels', 'epoch_id', 'subject_id'.
        missing_threshold: Threshold fraction of missing data (e.g., 0.05 for 5%).
        
    Returns:
        DataFrame with epochs flagged as having too much missing data (is_excluded=True).
        The returned DataFrame is a copy to avoid modifying the original.
    """
    if 'n_missing_sensors' not in epochs_metadata.columns or 'n_channels' not in epochs_metadata.columns:
        raise ValueError("epochs_metadata must contain 'n_missing_sensors' and 'n_channels' columns.")
    
    # Calculate missing fraction
    df = epochs_metadata.copy()
    # Avoid division by zero
    df['missing_fraction'] = df['n_missing_sensors'] / (df['n_channels'] + 1e-9)
    
    # Flag epochs exceeding threshold (FR-003: EXCLUDE them)
    df['is_excluded'] = df['missing_fraction'] > missing_threshold
    
    # Log statistics
    total_epochs = len(df)
    excluded_epochs = df['is_excluded'].sum()
    retention_rate = 1.0 - (excluded_epochs / total_epochs) if total_epochs > 0 else 0.0
    
    print(f"Validity Check: Total epochs={total_epochs}, Excluded={excluded_epochs} ({excluded_epochs/total_epochs*100:.2f}%)")
    print(f"Validity Check: Retention rate: {retention_rate*100:.2f}%")
    
    if retention_rate < 0.70:
        print(f"WARNING: Retention rate ({retention_rate*100:.2f}%) is below 70% threshold.")
    
    return df

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
    df = epochs_metadata.copy()
    df['has_missing_sensors'] = df['n_missing_sensors'] > 0
    return df

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

def calculate_file_checksum(filepath: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_state_checksums(output_path: str, state_path: str = "state/pipeline_state.yaml"):
    """
    Update the project state file with the checksum of the output artifact.
    This satisfies Constitution Principle VI (traceability).
    """
    if not os.path.exists(output_path):
        print(f"Warning: Output file {output_path} does not exist, skipping state update.")
        return

    checksum = calculate_file_checksum(output_path)
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    state_data = {}
    if os.path.exists(state_path):
        import yaml
        with open(state_path, 'r') as f:
            state_data = yaml.safe_load(f) or {}
    
    # Ensure state structure exists
    if 'artifacts' not in state_data:
        state_data['artifacts'] = {}
    
    artifact_name = os.path.basename(output_path)
    state_data['artifacts'][artifact_name] = {
        'checksum': checksum,
        'updated_at': timestamp,
        'path': output_path
    }
    
    state_data['updated_at'] = timestamp
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    
    import yaml
    with open(state_path, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False)
    
    print(f"Updated state checksum for {artifact_name} in {state_path}")

def main():
    """
    Main entry point for the validity check script.
    Reads clean epochs metadata, applies exclusion logic, and saves the filtered dataset.
    """
    # Configuration (simplified for script execution, can be loaded from config.py)
    input_path = "data/processed/epochs_metadata.csv"
    output_path = "data/processed/epochs_metadata_filtered.csv"
    missing_threshold = 0.05  # 5%

    if not os.path.exists(input_path):
        # If the file doesn't exist, we cannot run the check.
        # In a real pipeline, this would be an error raised by the orchestrator.
        # For this task, we simulate the existence of a minimal metadata file if missing
        # to demonstrate the logic, but the requirement is to process REAL data.
        # If real data is missing, we fail loudly.
        print(f"Error: Input file {input_path} not found. Please ensure T014 (preprocess) has run.")
        sys.exit(1)

    print(f"Loading epochs metadata from {input_path}...")
    df = pd.read_csv(input_path)

    print(f"Running validity check with threshold {missing_threshold}...")
    df_filtered = identify_missing_sensor_epochs(df, missing_threshold=missing_threshold)

    # Save the filtered dataframe
    df_filtered.to_csv(output_path, index=False)
    print(f"Filtered metadata saved to {output_path}")
    
    # Update state
    update_state_checksums(output_path)

    # Return summary for verification
    excluded_count = df_filtered['is_excluded'].sum()
    total_count = len(df_filtered)
    print(f"Summary: Excluded {excluded_count}/{total_count} epochs.")

if __name__ == "__main__":
    main()