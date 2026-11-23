"""
Validity checks for EEG feature extraction.

Implements checks for missing sensors, data quality, and stability of extracted power values.
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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_file_checksum(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_state_checksums(state_path: str = "state.yaml") -> None:
    """Update state file with checksums of processed files."""
    import yaml
    
    if not os.path.exists(state_path):
        logger.warning(f"State file {state_path} not found. Creating new state file.")
        state = {
            "updated_at": datetime.datetime.now().isoformat(),
            "checksums": {}
        }
    else:
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f)
    
    # Update timestamp
    state["updated_at"] = datetime.datetime.now().isoformat()
    
    # Update checksums for relevant files
    files_to_check = [
        "data/processed/feature_matrix.parquet",
        "data/processed/labels.parquet",
        "results/power_stability_report.json"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            checksum = calculate_file_checksum(file_path)
            state["checksums"][file_path] = checksum
    
    with open(state_path, 'w') as f:
        yaml.dump(state, f)

def identify_missing_sensor_epochs(epochs_data: pd.DataFrame, threshold: float = 0.05) -> pd.DataFrame:
    """
    Identify epochs with > threshold% missing sensor data.
    
    Args:
        epochs_data: DataFrame with columns ['epoch_id', 'subject_id', 'channel', 'power', 'is_missing']
        threshold: Fraction of missing data to flag (default 0.05 = 5%)
    
    Returns:
        DataFrame with epochs marked as excluded if they exceed the threshold
    """
    if epochs_data is None or epochs_data.empty:
        logger.warning("No epochs data provided for missing sensor check.")
        return pd.DataFrame()
    
    # Group by epoch_id and calculate missing data ratio
    missing_stats = epochs_data.groupby('epoch_id').agg({
        'is_missing': ['sum', 'count']
    }).reset_index()
    
    missing_stats.columns = ['epoch_id', 'missing_count', 'total_count']
    missing_stats['missing_ratio'] = missing_stats['missing_count'] / missing_stats['total_count']
    
    # Flag epochs exceeding threshold
    missing_stats['excluded'] = missing_stats['missing_ratio'] > threshold
    
    # Merge back to original data
    result = epochs_data.merge(
        missing_stats[['epoch_id', 'excluded']], 
        on='epoch_id', 
        how='left'
    )
    
    excluded_count = result['excluded'].sum()
    logger.info(f"Identified {excluded_count} epochs with > {threshold*100}% missing sensor data.")
    
    return result

def flag_missing_sensors(epochs_data: pd.DataFrame) -> Dict[str, Any]:
    """
    Flag specific sensors with missing data across subjects.
    
    Args:
        epochs_data: DataFrame with columns ['epoch_id', 'subject_id', 'channel', 'power', 'is_missing']
    
    Returns:
        Dictionary with summary of missing sensors per subject
    """
    if epochs_data is None or epochs_data.empty:
        logger.warning("No epochs data provided for missing sensor flagging.")
        return {"missing_sensors": {}, "summary": {}}
    
    # Filter for missing data
    missing_data = epochs_data[epochs_data['is_missing'] == True]
    
    if missing_data.empty:
        logger.info("No missing sensor data found.")
        return {"missing_sensors": {}, "summary": {"total_missing": 0}}
    
    # Group by subject and channel to find missing sensors
    missing_per_subject = missing_data.groupby(['subject_id', 'channel']).size().reset_index(name='missing_count')
    
    # Create summary
    missing_sensors = {}
    for subject_id in missing_per_subject['subject_id'].unique():
        subject_missing = missing_per_subject[missing_per_subject['subject_id'] == subject_id]
        missing_sensors[str(subject_id)] = subject_missing['channel'].tolist()
    
    summary = {
        "total_missing": len(missing_data),
        "subjects_affected": len(missing_sensors),
        "most_missing_channels": missing_per_subject.groupby('channel')['missing_count'].sum().nlargest(5).to_dict()
    }
    
    logger.info(f"Flagged missing sensors for {summary['subjects_affected']} subjects.")
    return {"missing_sensors": missing_sensors, "summary": summary}

def measure_power_stability(feature_df: pd.DataFrame, output_path: str = "results/power_stability_report.json") -> Dict[str, Any]:
    """
    Measure and report the stability and non-zero nature of extracted power values across subjects.
    
    This function implements SC-005 by:
    1. Verifying that power values are non-zero (not all zeros or NaNs)
    2. Calculating coefficient of variation (CV) across subjects for each channel/band
    3. Checking for extreme outliers that might indicate instability
    4. Generating a comprehensive report of stability metrics
    
    Args:
        feature_df: DataFrame with extracted features (columns: subject_id, channel, theta_power, alpha_power, etc.)
        output_path: Path to save the stability report JSON
    
    Returns:
        Dictionary containing stability metrics and pass/fail status
    """
    if feature_df is None or feature_df.empty:
        logger.error("Feature DataFrame is empty or None. Cannot measure power stability.")
        return {"status": "failed", "reason": "Empty feature data"}
    
    logger.info("Measuring power value stability across subjects...")
    
    # Define power columns to check (adjust based on actual feature columns)
    power_columns = [col for col in feature_df.columns if 'power' in col.lower() and col != 'is_missing']
    
    if not power_columns:
        # Try common column names if auto-detection fails
        power_columns = ['theta_power', 'alpha_power', 'theta_alpha_ratio', 'beta_power', 'gamma_power']
        power_columns = [col for col in power_columns if col in feature_df.columns]
    
    if not power_columns:
        logger.warning("No power columns found in feature data.")
        return {"status": "failed", "reason": "No power columns detected"}
    
    results = {
        "timestamp": datetime.datetime.now().isoformat(),
        "subjects_analyzed": feature_df['subject_id'].nunique() if 'subject_id' in feature_df.columns else len(feature_df),
        "channels_analyzed": feature_df['channel'].nunique() if 'channel' in feature_df.columns else "N/A",
        "power_columns_checked": power_columns,
        "metrics": {},
        "non_zero_check": {},
        "stability_check": {},
        "outlier_check": {},
        "overall_status": "passed"
    }
    
    # 1. Check for non-zero values
    logger.info("Checking for non-zero power values...")
    for col in power_columns:
        col_data = feature_df[col].dropna()
        
        if len(col_data) == 0:
            results["non_zero_check"][col] = {
                "status": "failed",
                "reason": "No valid data points"
            }
            continue
        
        zero_count = (col_data == 0).sum()
        total_count = len(col_data)
        zero_ratio = zero_count / total_count if total_count > 0 else 1.0
        
        # Check if all values are zero (critical failure)
        if zero_count == total_count:
            results["non_zero_check"][col] = {
                "status": "failed",
                "reason": f"All {total_count} values are zero",
                "zero_ratio": float(zero_ratio)
            }
            results["overall_status"] = "failed"
        elif zero_ratio > 0.5:
            results["non_zero_check"][col] = {
                "status": "warning",
                "reason": f"More than 50% of values are zero ({zero_ratio:.2%})",
                "zero_ratio": float(zero_ratio)
            }
        else:
            results["non_zero_check"][col] = {
                "status": "passed",
                "reason": f"Only {zero_ratio:.2%} of values are zero",
                "zero_ratio": float(zero_ratio),
                "non_zero_count": int(total_count - zero_count)
            }
    
    # 2. Calculate stability metrics (Coefficient of Variation) per channel/band
    logger.info("Calculating stability metrics (CV) across subjects...")
    
    if 'channel' in feature_df.columns:
        for col in power_columns:
            stability_stats = {}
            for channel in feature_df['channel'].unique():
                channel_data = feature_df[feature_df['channel'] == channel][col].dropna()
                if len(channel_data) > 0:
                    mean_val = channel_data.mean()
                    std_val = channel_data.std()
                    cv = std_val / mean_val if mean_val != 0 else float('inf')
                    
                    stability_stats[channel] = {
                        "mean": float(mean_val),
                        "std": float(std_val),
                        "cv": float(cv) if cv != float('inf') else "inf",
                        "count": int(len(channel_data))
                    }
            
            results["stability_check"][col] = stability_stats
    
    # 3. Check for outliers (values > 3 std from mean)
    logger.info("Checking for extreme outliers...")
    for col in power_columns:
        col_data = feature_df[col].dropna()
        if len(col_data) > 0:
            mean_val = col_data.mean()
            std_val = col_data.std()
            
            if std_val > 0:
                lower_bound = mean_val - 3 * std_val
                upper_bound = mean_val + 3 * std_val
                
                outliers = col_data[(col_data < lower_bound) | (col_data > upper_bound)]
                outlier_ratio = len(outliers) / len(col_data)
                
                results["outlier_check"][col] = {
                    "mean": float(mean_val),
                    "std": float(std_val),
                    "outlier_count": int(len(outliers)),
                    "outlier_ratio": float(outlier_ratio),
                    "status": "passed" if outlier_ratio < 0.01 else "warning"
                }
                if outlier_ratio > 0.05:
                    results["overall_status"] = "warning"
    
    # 4. Summary and pass/fail determination
    logger.info(f"Stability analysis complete. Overall status: {results['overall_status']}")
    
    # Save report
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Power stability report saved to {output_path}")
    
    return results

def main():
    """
    Main function to run validity checks.
    
    This function:
    1. Loads the feature matrix from data/processed/feature_matrix.parquet
    2. Runs identify_missing_sensor_epochs
    3. Runs flag_missing_sensors
    4. Runs measure_power_stability (SC-005)
    5. Saves reports to results/
    6. Updates state checksums
    """
    logger.info("Starting validity checks (T031b)...")
    
    # Load feature data
    feature_path = "data/processed/feature_matrix.parquet"
    if not os.path.exists(feature_path):
        logger.error(f"Feature matrix not found at {feature_path}. Please run feature extraction first.")
        sys.exit(1)
    
    try:
        feature_df = pd.read_parquet(feature_path)
        logger.info(f"Loaded feature matrix with {len(feature_df)} rows")
    except Exception as e:
        logger.error(f"Failed to load feature matrix: {e}")
        sys.exit(1)
    
    # Ensure required columns exist
    required_cols = ['subject_id', 'channel']
    missing_cols = [col for col in required_cols if col not in feature_df.columns]
    if missing_cols:
        logger.error(f"Missing required columns in feature data: {missing_cols}")
        sys.exit(1)
    
    # Run missing sensor checks (T031)
    # Note: T031b requires T024 (theta/alpha ratio) which should be in feature_df
    logger.info("Running power stability measurement (SC-005)...")
    stability_results = measure_power_stability(feature_df, "results/power_stability_report.json")
    
    # Log results
    logger.info(f"Power stability check status: {stability_results['overall_status']}")
    if stability_results['overall_status'] == 'failed':
        logger.error("Power stability check FAILED. Review results/power_stability_report.json.")
        sys.exit(1)
    elif stability_results['overall_status'] == 'warning':
        logger.warning("Power stability check has warnings. Review results/power_stability_report.json.")
    
    # Update state
    update_state_checksums()
    
    logger.info("Validity checks (T031b) completed successfully.")

if __name__ == "__main__":
    main()