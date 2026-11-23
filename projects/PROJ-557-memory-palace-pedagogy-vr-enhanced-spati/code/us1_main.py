"""
US1 Main Orchestration Script

Orchestrates the preprocessing of raw pupil data and the generation of the
Cognitive Load Index (CLI) time series.

This script:
1. Loads raw data from data/raw/ (downloaded by T004).
2. Applies preprocessing steps (blink removal, filtering, baseline correction, luminance normalization).
3. Computes the CLI (moving average z-score) per window.
4. Identifies high-load windows and flags outliers.
5. Outputs the final CLI time series to data/derived/cli_time_series.parquet.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any

import pandas as pd
import numpy as np

# Import project modules
from config import get_config, set_random_seed
from utils.logging import setup_pipeline_logger, log_step, log_error
from preprocessing import (
    remove_blinks,
    low_pass_filter,
    baseline_correct,
    ingest_screen_luminance_logs,
    preprocess_luminance_for_window,
    normalize_luminance_algorithm
)
from cli_engine import (
    compute_moving_average_zscore,
    identify_high_load_windows,
    compute_outlier_flags,
    process_window_data
)
from data_model import Window

def load_raw_pupil_data(config: Any) -> pd.DataFrame:
    """
    Loads the raw pupil data from the downloaded dataset.
    Assumes T004 has successfully downloaded ds004041 to data/raw/.
    """
    raw_dir = config.data_raw_dir
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")

    # Look for pupil data files (typically .tsv or .csv in OpenNeuro datasets)
    # ds004041 structure: sub-*/ses-*/func/sub-_*_task-reading_pupil.tsv
    pupil_files = list(raw_dir.rglob("sub-*/*/*pupil*.tsv"))
    
    if not pupil_files:
        # Fallback for different directory structures or if files are directly in raw
        pupil_files = list(raw_dir.rglob("*pupil*.tsv"))
    
    if not pupil_files:
        raise FileNotFoundError(
            f"No pupil data files (.tsv) found in {raw_dir}. "
            "Ensure T004 (download) has completed successfully."
        )

    log_step("load_raw_data", f"Found {len(pupil_files)} pupil data files.")
    
    # Concatenate all files into a single DataFrame
    # Assuming consistent schema across subjects/sessions
    dfs = []
    for f in pupil_files:
        # OpenNeuro pupil data usually has columns: time, x, y, pupil_diameter, etc.
        # We need to handle potential subject/session metadata extraction from filename
        df = pd.read_csv(f, sep='\t')
        df['source_file'] = f.name
        dfs.append(df)
    
    raw_df = pd.concat(dfs, ignore_index=True)
    log_step("load_raw_data", f"Loaded {len(raw_df)} rows of raw pupil data.")
    return raw_df

def run_preprocessing(raw_df: pd.DataFrame, config: Any) -> pd.DataFrame:
    """
    Runs the full preprocessing pipeline on raw pupil data.
    """
    log_step("preprocessing", "Starting preprocessing pipeline.")
    
    # 1. Remove blinks
    log_step("preprocessing", "Removing blinks...")
    clean_df = remove_blinks(raw_df)
    
    # 2. Low-pass filter (4Hz cutoff)
    log_step("preprocessing", "Applying 4Hz low-pass filter...")
    filtered_df = low_pass_filter(clean_df, cutoff_hz=4.0)
    
    # 3. Baseline correction
    log_step("preprocessing", "Performing baseline correction...")
    corrected_df = baseline_correct(filtered_df, baseline_window_sec=5.0)
    
    # 4. Luminance normalization
    # First, ingest luminance logs (if available in the dataset)
    # ds004041 may contain screen luminance logs. We attempt to ingest them.
    luminance_logs = ingest_screen_luminance_logs(config.data_raw_dir)
    
    if luminance_logs is not None and not luminance_logs.empty:
        log_step("preprocessing", "Normalizing luminance...")
        # Apply normalization algorithm
        normalized_df = normalize_routine(corrected_df, luminance_logs)
    else:
        log_step("preprocessing", "No luminance logs found. Skipping normalization.")
        normalized_df = corrected_df
    
    log_step("preprocessing", "Preprocessing complete.")
    return normalized_df

def normalize_routine(df: pd.DataFrame, luminance_logs: pd.DataFrame) -> pd.DataFrame:
    """
    Wrapper to apply luminance normalization algorithm to the dataframe.
    """
    # Prepare luminance for the window (aggregate if needed)
    # Assuming df has a 'time' column and luminance_logs has 'time' and 'luminance'
    # We need to align them. For simplicity, we assume the logs are continuous
    # and we apply the algorithm to the whole series.
    
    # The algorithm expects a series of luminance values
    # We map the luminance logs to the pupil data timestamps via interpolation
    # or simply apply the algorithm to the pupil data if luminance is constant.
    # For ds004041, we assume we can compute a normalization factor.
    
    # Simplified approach: Use the algorithm to compute a normalization factor
    # based on the luminance logs, then apply to pupil diameter.
    norm_factor = normalize_luminance_algorithm(luminance_logs['luminance'].values)
    
    # Apply factor to pupil diameter (assuming column 'pupil_diameter')
    if 'pupil_diameter' in df.columns:
        df['pupil_diameter_normalized'] = df['pupil_diameter'] / norm_factor
    else:
        # Fallback if column name differs
        pupil_col = df.select_dtypes(include=[np.number]).columns[0]
        df['pupil_diameter_normalized'] = df[pupil_col] / norm_factor
        
    return df

def compute_cli(preprocessed_df: pd.DataFrame, config: Any) -> pd.DataFrame:
    """
    Computes the Cognitive Load Index (CLI) time series.
    """
    log_step("cli_engine", "Computing CLI time series.")
    
    # Define window parameters (e.g., 2-second windows, 1-second stride)
    window_size_sec = 2.0
    stride_sec = 1.0
    
    # Process data into windows
    windowed_data = process_window_data(
        preprocessed_df,
        window_size_sec=window_size_sec,
        stride_sec=stride_sec,
        value_column='pupil_diameter_normalized' if 'pupil_diameter_normalized' in preprocessed_df.columns else 'pupil_diameter'
    )
    
    if windowed_data.empty:
        log_error("cli_engine", "No windows generated. Check preprocessing output.")
        return pd.DataFrame()
    
    # Compute moving average z-score for each window
    cli_df = compute_moving_average_zscore(windowed_data, window_size=10)
    
    # Identify high-load windows (threshold > 0.5 SD)
    high_load_mask = identify_high_load_windows(cli_df, threshold_sd=0.5)
    cli_df['is_high_load'] = high_load_mask
    
    # Flag outliers (> 3 SD)
    outlier_flags = compute_outlier_flags(cli_df, threshold_sd=3.0)
    cli_df['is_outlier'] = outlier_flags
    
    # Filter out outliers if required by config (usually kept for analysis but flagged)
    # For the time series output, we keep all rows but flag them.
    
    log_step("cli_engine", f"Generated {len(cli_df)} windows. "
                          f"High load: {high_load_mask.sum()}, Outliers: {outlier_flags.sum()}")
    
    return cli_df

def save_results(cli_df: pd.DataFrame, config: Any) -> str:
    """
    Saves the CLI time series to the derived directory.
    """
    output_path = config.data_derived_dir / "cli_time_series.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    cli_df.to_parquet(output_path, index=False)
    log_step("save_results", f"Saved CLI time series to {output_path}")
    return str(output_path)

def main():
    """
    Main entry point for US1 orchestration.
    """
    # Initialize config and logging
    config = get_config()
    set_random_seed(config.random_seed)
    logger = setup_pipeline_logger("us1_main", config.log_dir)
    
    log_step("us1_main", "Starting US1: Cognitive Load Index Calculation")
    
    try:
        # 1. Load Raw Data
        raw_df = load_raw_pupil_data(config)
        
        # 2. Preprocess
        preprocessed_df = run_preprocessing(raw_df, config)
        
        # 3. Compute CLI
        cli_df = compute_cli(preprocessed_df, config)
        
        if cli_df.empty:
            raise RuntimeError("CLI computation resulted in an empty DataFrame.")
        
        # 4. Save Results
        output_path = save_results(cli_df, config)
        
        log_step("us1_main", "US1 completed successfully.")
        print(f"Output written to: {output_path}")
        
    except Exception as e:
        log_error("us1_main", f"Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()