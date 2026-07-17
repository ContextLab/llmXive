"""
Preprocessing module for flight delay data.
Handles loading, cleaning, filtering, and preparing data for analysis.
"""
import os
import sys
import math
import json
import logging
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from data_loader import download_bts_data
from config import get_bts_url, RANDOM_SEED
from utils import check_memory_limit, log_peak_memory, PipelineError

# Set random seed for reproducibility
np.random.seed(RANDOM_SEED)

logger = logging.getLogger(__name__)

# Constants
MEMORY_LIMIT_GB = 6.5
ANOMALY_THRESHOLD = 1440  # 24 hours in minutes
DATA_ERROR_THRESHOLD = 10000  # 10,000 minutes
MIN_RETENTION_RATE = 0.95
COMMERCIAL_CARRIERS = ['AA', 'DL', 'UA', 'WN', 'AS', 'B6', 'NK', 'F9', 'HA', 'SY']

def estimate_csv_memory(file_path: str) -> float:
    """Estimate memory usage for loading a CSV file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    # Estimate: 1.5x file size for pandas DataFrame overhead
    estimated_gb = (file_size_mb * 1.5) / 1024
    return estimated_gb

def load_large_csv(file_path: str, chunksize: int = 100000) -> pd.DataFrame:
    """Load a large CSV file in chunks to manage memory."""
    check_memory_limit(MEMORY_LIMIT_GB)
    
    chunks = []
    total_rows = 0
    for chunk in pd.read_csv(file_path, chunksize=chunksize):
        chunks.append(chunk)
        total_rows += len(chunk)
        if total_rows % 1000000 == 0:
            logger.info(f"Loaded {total_rows:,} rows...")
    
    df = pd.concat(chunks, ignore_index=True)
    log_peak_memory()
    return df

def create_memmap_array(file_path: str, dtype: np.dtype = np.float64) -> np.memmap:
    """Create a memory-mapped array for large datasets."""
    check_memory_limit(MEMORY_LIMIT_GB)
    
    # Estimate number of rows
    with open(file_path, 'r') as f:
        num_rows = sum(1 for _ in f) - 1  # Subtract header
    
    # Create memmap
    memmap_path = file_path.replace('.csv', '.memmap')
    shape = (num_rows,)
    mm = np.memmap(memmap_path, dtype=dtype, mode='w+', shape=shape)
    
    # Load data into memmap
    df = pd.read_csv(file_path)
    mm[:] = df['ArrDelay'].values
    del df
    
    return mm

def preprocess_flight_delays(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Clean and preprocess flight delay data.
    
    Steps:
    1. Filter commercial US flights
    2. Compute total_delay = ArrDelay + DepDelay
    3. Treat missing as 0
    4. Remove negative delays
    5. Flag data errors and anomalies
    6. Calculate retention rate
    
    Returns:
      Tuple of (processed_df, summary_stats)
    """
    logger.info("Starting preprocessing...")
    
    # Store original row count
    original_count = len(df)
    logger.info(f"Original dataset size: {original_count:,} rows")
    
    # Filter for commercial US carriers
    if 'UniqueCarrier' in df.columns:
        commercial_mask = df['UniqueCarrier'].isin(COMMERCIAL_CARRIERS)
        df = df[commercial_mask].copy()
        logger.info(f"After carrier filter: {len(df):,} rows")
    
    # Handle missing values in delay columns
    delay_cols = ['ArrDelay', 'DepDelay']
    for col in delay_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0)
        else:
            # If column doesn't exist, create with zeros
            df[col] = 0
    
    # Compute total delay
    if 'ArrDelay' in df.columns and 'DepDelay' in df.columns:
        df['total_delay'] = df['ArrDelay'] + df['DepDelay']
    else:
        # Fallback: use ArrDelay if DepDelay missing
        df['total_delay'] = df.get('ArrDelay', 0)
    
    # Remove negative delays (data errors)
    initial_count = len(df)
    df = df[df['total_delay'] >= 0]
    removed_negative = initial_count - len(df)
    logger.info(f"Removed {removed_negative:,} negative delays")
    
    # Flag data errors (>10,000 min)
    df['is_data_error'] = df['total_delay'] > DATA_ERROR_THRESHOLD
    data_error_count = df['is_data_error'].sum()
    logger.info(f"Flagged {data_error_count:,} data errors (>10,000 min)")
    
    # Flag anomalies (>1,440 min but <= 10,000 min)
    df['is_anomaly'] = (df['total_delay'] > ANOMALY_THRESHOLD) & (df['total_delay'] <= DATA_ERROR_THRESHOLD)
    anomaly_count = df['is_anomaly'].sum()
    logger.info(f"Flagged {anomaly_count:,} anomalies (>24h)")
    
    # Exclude data errors from primary set (keep for reference)
    primary_df = df[~df['is_data_error']].copy()
    
    # Calculate retention rate
    valid_count = len(primary_df)
    retention_rate = valid_count / original_count if original_count > 0 else 0
    
    logger.info(f"Retention rate: {retention_rate:.2%} ({valid_count:,} / {original_count:,})")
    
    # Check retention rate threshold
    if retention_rate < MIN_RETENTION_RATE:
        error_msg = f"Retention Rate Failure: {retention_rate:.2%} < {MIN_RETENTION_RATE:.2%}"
        logger.error(error_msg)
        raise SystemExit(1)
    
    # Create zero-excluded subset for sensitivity analysis
    zero_delay_count = (primary_df['total_delay'] == 0).sum()
    zero_inflation_rate = zero_delay_count / len(primary_df) if len(primary_df) > 0 else 0
    
    zero_excluded_df = primary_df[primary_df['total_delay'] > 0].copy()
    logger.info(f"Zero delays: {zero_delay_count:,} ({zero_inflation_rate:.2%})")
    logger.info(f"Zero-excluded subset size: {len(zero_excluded_df):,} rows")
    
    # Prepare summary statistics
    summary_stats = {
        'original_count': int(original_count),
        'after_carrier_filter': int(len(df)),
        'removed_negative': int(removed_negative),
        'data_error_count': int(data_error_count),
        'anomaly_count': int(anomaly_count),
        'valid_count': int(valid_count),
        'zero_delay_count': int(zero_delay_count),
        'zero_excluded_count': int(len(zero_excluded_df)),
        'retention_rate': float(retention_rate),
        'zero_inflation_rate': float(zero_inflation_rate),
        'is_zero_inflated': bool(zero_inflation_rate > 0.1)  # Flag if >10% zeros
    }
    
    return primary_df, zero_excluded_df, summary_stats

def save_summary_report(stats: Dict[str, Any], output_path: str) -> None:
    """Save summary statistics to JSON file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Summary report saved to {output_path}")

def main():
    """Main entry point for preprocessing stage."""
    parser = argparse.ArgumentParser(description='Preprocess flight delay data')
    parser.add_argument('--input', type=str, required=True, help='Input CSV file path')
    parser.add_argument('--output', type=str, required=True, help='Output CSV file path')
    parser.add_argument('--summary', type=str, default='data/processed/summary_report.json', 
                      help='Output summary report path')
    parser.add_argument('--zero-excluded-output', type=str, default='data/processed/cleaned_delays_no_zeros.csv',
                      help='Output path for zero-excluded subset')
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('data/logs/pipeline.log'),
            logging.StreamHandler()
        ]
    )
    
    try:
        # Load data
        logger.info(f"Loading data from {args.input}")
        df = load_large_csv(args.input)
        
        # Preprocess
        primary_df, zero_excluded_df, summary_stats = preprocess_flight_delays(df)
        
        # Save primary cleaned data
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        primary_df.to_csv(args.output, index=False)
        logger.info(f"Primary cleaned data saved to {args.output}")
        
        # Save zero-excluded subset
        Path(args.zero_excluded_output).parent.mkdir(parents=True, exist_ok=True)
        zero_excluded_df.to_csv(args.zero_excluded_output, index=False)
        logger.info(f"Zero-excluded subset saved to {args.zero_excluded_output}")
        
        # Save summary report
        save_summary_report(summary_stats, args.summary)
        
        logger.info("Preprocessing completed successfully")
        
    except Exception as e:
        logger.error(f"Pipeline failed with error: {str(e)}")
        raise

if __name__ == '__main__':
    main()