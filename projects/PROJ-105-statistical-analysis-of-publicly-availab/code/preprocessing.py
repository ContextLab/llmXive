import os
import sys
import math
from pathlib import Path
from typing import Optional, Tuple
import pandas as pd
import numpy as np

# Import from local modules to ensure consistency with project structure
from config import RANDOM_SEED, MEMORY_LIMIT_GB, TARGET_YEAR
from utils import check_memory_limit, log_peak_memory, setup_logging

# Setup logging
logger = setup_logging()

def estimate_csv_memory(file_path: str) -> float:
    """
    Estimate the memory footprint of a CSV file in GB.
    Uses a heuristic based on file size and a safety factor for pandas overhead.
    """
    file_size_bytes = os.path.getsize(file_path)
    # Heuristic: pandas DataFrame often uses 1.5x - 2x the raw CSV size in memory
    # due to object overhead, index, and string storage.
    estimated_gb = (file_size_bytes * 2.0) / (1024 ** 3)
    return estimated_gb

def load_large_csv(file_path: str, chunksize: int = 100000) -> pd.DataFrame:
    """
    Load a large CSV file in chunks to avoid memory spikes.
    Returns a single concatenated DataFrame.
    """
    logger.info(f"Loading large CSV in chunks: {file_path}")
    chunks = []
    total_rows = 0
    
    for chunk in pd.read_csv(file_path, chunksize=chunksize):
        check_memory_limit(MEMORY_LIMIT_GB)
        chunks.append(chunk)
        total_rows += len(chunk)
        if total_rows % 1000000 == 0:
            logger.info(f"Loaded {total_rows:,} rows...")
    
    df = pd.concat(chunks, ignore_index=True)
    log_peak_memory()
    return df

def create_memmap_array(data: np.ndarray, filename: str) -> np.ndarray:
    """
    Create a memory-mapped array from a numpy array to save RAM.
    """
    shape = data.shape
    dtype = data.dtype
    memmap = np.memmap(filename, dtype=dtype, mode='w+', shape=shape)
    memmap[:] = data[:]
    del memmap
    # Return read-only memmap
    return np.memmap(filename, dtype=dtype, mode='r', shape=shape)

def preprocess_flight_delays(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """
    Core preprocessing logic for flight delay data.
    
    Steps:
    1. Filter for commercial US flights (CarrierType == 'U').
    2. Compute total_delay = ArrDelay + DepDelay.
    3. Treat missing values in delay columns as 0.
    4. Remove negative delays.
    5. Flag data errors (>10,000 min) and anomalies (>1,440 min).
    6. Exclude data errors from the primary set.
    7. Calculate retention rate. Raise SystemExit if < 95%.
    8. Create a zero-excluded subset for sensitivity analysis.
    9. Flag zero-inflation if the proportion of zero delays is significant.
    
    Returns:
      Tuple of (processed_df, summary_stats)
    """
    logger.info("Starting preprocessing pipeline...")
    
    initial_count = len(df)
    
    # 1. Filter commercial US flights
    # Assuming 'CarrierType' column exists based on typical BTS data
    if 'CarrierType' in df.columns:
        df = df[df['CarrierType'] == 'U'].copy()
    
    # 2. Compute total_delay
    # Handle potential missing values by filling with 0 first
    if 'ArrDelay' not in df.columns or 'DepDelay' not in df.columns:
        raise ValueError("Required columns 'ArrDelay' and 'DepDelay' not found in dataset.")
    
    df['ArrDelay'] = pd.to_numeric(df['ArrDelay'], errors='coerce').fillna(0)
    df['DepDelay'] = pd.to_numeric(df['DepDelay'], errors='coerce').fillna(0)
    
    df['total_delay'] = df['ArrDelay'] + df['DepDelay']
    
    # 3. Remove negative delays
    # Negative delays usually indicate early arrivals/departures, treated as 0 or removed
    # Per task: "Remove negative delays"
    df = df[df['total_delay'] >= 0].copy()
    
    # 4. Flag data errors and anomalies
    # Data error: > 10,000 minutes (implausible)
    # Anomaly: > 1,440 minutes (24 hours)
    df['is_data_error'] = df['total_delay'] > 10000
    df['is_anomaly'] = df['total_delay'] > 1440
    
    # 5. Exclude data errors from primary set
    primary_df = df[~df['is_data_error']].copy()
    anomaly_count = primary_df['is_anomaly'].sum()
    
    # 6. Calculate retention rate
    # Retention = (valid records in primary set) / (total records initially loaded)
    # Note: "valid" here implies after filtering errors and negatives
    retention_rate = len(primary_df) / initial_count if initial_count > 0 else 0.0
    
    if retention_rate < 0.95:
        error_msg = f"Retention Rate Failure: {retention_rate:.4f} < 0.95"
        logger.error(error_msg)
        raise SystemExit(error_msg)
    
    # 7. Create zero-excluded subset for sensitivity analysis
    # This is crucial for fitting distributions that cannot handle zeros (e.g., Log-Normal, Pareto)
    non_zero_df = primary_df[primary_df['total_delay'] > 0].copy()
    zero_count = len(primary_df) - len(non_zero_df)
    zero_proportion = zero_count / len(primary_df) if len(primary_df) > 0 else 0.0
    
    # 8. Flag zero-inflation
    # Heuristic: If > 20% of delays are zero, it's considered zero-inflated
    # This is a domain-specific threshold for sensitivity analysis flagging
    ZERO_INFLATION_THRESHOLD = 0.20
    is_zero_inflated = zero_proportion > ZERO_INFLATION_THRESHOLD
    
    logger.info(f"Preprocessing complete. Retention Rate: {retention_rate:.2%}")
    logger.info(f"Zero delays: {zero_count} ({zero_proportion:.2%})")
    logger.info(f"Zero-inflation flag: {is_zero_inflated}")
    
    summary_stats = {
        "initial_count": initial_count,
        "primary_count": len(primary_df),
        "non_zero_count": len(non_zero_df),
        "zero_count": int(zero_count),
        "zero_proportion": float(zero_proportion),
        "is_zero_inflated": is_zero_inflated,
        "retention_rate": float(retention_rate),
        "anomaly_count": int(anomaly_count)
    }
    
    return primary_df, non_zero_df, summary_stats

def main():
    """
    Main entry point for preprocessing script.
    Downloads data, processes it, and saves outputs.
    """
    # Check memory before starting
    check_memory_limit(MEMORY_LIMIT_GB)
    
    # 1. Load data (assuming download happened or file exists)
    # For this task, we assume the file is already downloaded by T013/T014
    # or we call the download function if needed. 
    # Since T013/14 are done, we assume 'data/raw/flight_delays.csv' exists.
    raw_data_path = Path("data/raw/flight_delays.csv")
    
    if not raw_data_path.exists():
        logger.warning(f"Raw data not found at {raw_data_path}. Attempting download...")
        # Trigger download if missing (part of T013 logic, but safe to call here)
        from data_loader import download_bts_data
        download_bts_data()
    
    logger.info(f"Loading data from {raw_data_path}")
    df = load_large_csv(str(raw_data_path))
    
    # 2. Preprocess
    primary_df, non_zero_df, stats = preprocess_flight_delays(df)
    
    # 3. Save outputs
    # Save primary cleaned data
    cleaned_path = Path("data/processed/cleaned_delays.csv")
    cleaned_path.parent.mkdir(parents=True, exist_ok=True)
    primary_df.to_csv(cleaned_path, index=False)
    logger.info(f"Saved cleaned data to {cleaned_path}")
    
    # Save zero-excluded subset for sensitivity analysis
    zero_excluded_path = Path("data/processed/cleaned_delays_no_zeros.csv")
    non_zero_df.to_csv(zero_excluded_path, index=False)
    logger.info(f"Saved zero-excluded data to {zero_excluded_path}")
    
    # Save summary report
    report_path = Path("data/results/summary_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    import json
    with open(report_path, 'w') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Saved summary report to {report_path}")
    
    print(f"Loaded {stats['initial_count']} total records.")
    print(f"Valid records: {stats['primary_count']}")
    print(f"Zero-inflation detected: {stats['is_zero_inflated']}")
    print(f"Retention rate: {stats['retention_rate']:.2%}")

if __name__ == "__main__":
    main()
