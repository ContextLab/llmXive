"""
T023b: Compute descriptive statistics for explanation_engagement_time.

This script loads cleaned session data, computes mean and standard deviation
for the 'explanation_engagement_time_seconds' metric, and outputs the results
to data/processed/descriptive_stats.csv.

Per Spec FR-002 (Amended) and Plan Phase 3, this metric is reported 
descriptively only and is excluded from inferential ANOVA testing.
"""
import os
import sys
import pandas as pd
from pathlib import Path
import glob
import json
import argparse
import logging

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import get_logger

logger = get_logger(__name__)

def load_raw_session_data(input_path: str) -> pd.DataFrame:
    """
    Loads the cleaned sessions CSV.
    
    Args:
        input_path: Path to the cleaned sessions CSV.
        
    Returns:
        DataFrame containing session data.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If required columns are missing.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    required_cols = ['participant_id', 'interface_type', 'explanation_engagement_time_seconds']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {input_path}: {missing}")
    
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def compute_descriptive_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes descriptive statistics for explanation_engagement_time_seconds.
    
    Logic:
    - Group by interface_type.
    - Calculate mean and std for explanation_engagement_time_seconds.
    - Filter out rows where the value is NaN or 0 (if applicable, though 0 is valid for Traditional).
    - Note: For 'traditional' interface, engagement time should be 0 or null. 
      We compute stats for all groups where data exists.
      
    Returns:
        DataFrame with columns: interface_type, metric_name, mean, std, count.
    """
    # Ensure numeric type
    df['explanation_engagement_time_seconds'] = pd.to_numeric(
        df['explanation_engagement_time_seconds'], errors='coerce'
    )
    
    # Group by interface type
    grouped = df.groupby('interface_type')['explanation_engagement_time_seconds']
    
    results = []
    for interface, group in grouped:
        # Calculate stats
        mean_val = group.mean()
        std_val = group.std()
        count_val = group.count()
        
        # Handle NaNs (e.g., if all values were NaN)
        if pd.isna(mean_val):
            mean_val = 0.0
        if pd.isna(std_val):
            std_val = 0.0
            
        results.append({
            'interface_type': interface,
            'metric_name': 'explanation_engagement_time_seconds',
            'mean': mean_val,
            'std': std_val,
            'count': count_val
        })
        
    return pd.DataFrame(results)

def write_output(df_stats: pd.DataFrame, output_path: str):
    """
    Writes the descriptive statistics to a CSV file.
    
    Args:
        df_stats: DataFrame with statistics.
        output_path: Path to the output CSV file.
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    df_stats.to_csv(output_path, index=False)
    logger.info(f"Wrote descriptive stats to {output_path}")
    logger.info(f"Content:\n{df_stats.to_string()}")

def log_exclusion(df_raw: pd.DataFrame, df_cleaned: pd.DataFrame, log_path: str):
    """
    Logs any exclusion logic if applied (though T021a handles exclusion).
    This is for audit purposes.
    """
    # T021a already filtered incomplete sessions. 
    # We just log the final count used for this specific metric.
    with open(log_path, 'w') as f:
        f.write(f"Descriptive Stats Calculation Log\n")
        f.write(f"==================================\n")
        f.write(f"Total sessions used: {len(df_cleaned)}\n")
        f.write(f"Metric: explanation_engagement_time_seconds\n")
        f.write(f"Note: This metric is excluded from ANOVA per Spec Amendment T035a.\n")
    logger.info(f"Wrote exclusion log to {log_path}")

def main():
    parser = argparse.ArgumentParser(description="Compute descriptive stats for explanation engagement time.")
    parser.add_argument("--input", type=str, required=True, 
                        help="Path to cleaned sessions CSV (e.g., data/processed/cleaned_sessions.csv)")
    parser.add_argument("--output", type=str, required=True, 
                        help="Path to output descriptive stats CSV (e.g., data/processed/descriptive_stats.csv)")
    parser.add_argument("--log", type=str, default="data/processed/descriptive_stats_log.txt",
                        help="Path to log file")
    
    args = parser.parse_args()
    
    try:
        logger.info(f"Starting descriptive stats computation for task T023b")
        logger.info(f"Input: {args.input}")
        logger.info(f"Output: {args.output}")
        
        # Load data
        df = load_raw_session_data(args.input)
        
        # Compute stats
        df_stats = compute_descriptive_stats(df)
        
        # Write output
        write_output(df_stats, args.output)
        
        # Log audit info
        log_exclusion(df, df, args.log)
        
        logger.info("T023b completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during T023b: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()