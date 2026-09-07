"""
Task T022: Generate Summary CSV (baseline_comparison.csv)

Reads the aggregated baseline metrics from T021 (baseline_aggregation.csv)
and produces a summary CSV containing the core comparison columns:
condition, win_rate, avg_tokens, token_reduction_pct, threshold_met.

This script MUST be invoked by the run-book (e.g., in quickstart.md) to produce
the declared artifact data/processed/baseline_comparison.csv.
"""
import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/processed/generate_baseline_comparison.log')
    ]
)
logger = logging.getLogger(__name__)

# Paths
BASELINE_AGG_PATH = Path("data/processed/baseline_aggregation.csv")
OUTPUT_PATH = Path("data/processed/baseline_comparison.csv")

def load_aggregated_data():
    """
    Loads the aggregated baseline metrics from T021.
    """
    if not BASELINE_AGG_PATH.exists():
        logger.error(f"Input file not found: {BASELINE_AGG_PATH}")
        raise FileNotFoundError(
            f"Input file {BASELINE_AGG_PATH} not found. "
            "Ensure T021 (baseline_aggregation.csv) has been generated first."
        )
    
    try:
        df = pd.read_csv(BASELINE_AGG_PATH)
        logger.info(f"Loaded aggregated data from {BASELINE_AGG_PATH}. Rows: {len(df)}")
        return df
    except Exception as e:
        logger.error(f"Failed to read {BASELINE_AGG_PATH}: {e}")
        raise

def generate_summary(df):
    """
    Selects the required columns for the summary CSV.
    
    Expected columns in input (from T021):
    condition, win_rate, avg_tokens, std_dev_tokens, token_reduction_pct, 
    std_dev_token_savings, threshold_met
    
    Output columns:
    condition, win_rate, avg_tokens, token_reduction_pct, threshold_met
    """
    required_cols = [
        'condition', 
        'win_rate', 
        'avg_tokens', 
        'token_reduction_pct', 
        'threshold_met'
    ]
    
    # Validate presence of required columns
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns in input: {missing_cols}")
        raise ValueError(f"Input CSV missing columns: {missing_cols}")
    
    summary_df = df[required_cols].copy()
    
    # Ensure threshold_met is boolean or string representation
    # T021 logic sets this as boolean True/False based on reduction >= 30%
    if summary_df['threshold_met'].dtype == 'bool':
        summary_df['threshold_met'] = summary_df['threshold_met'].astype(str)
    
    logger.info(f"Generated summary with columns: {list(summary_df.columns)}")
    return summary_df

def save_summary(df):
    """
    Saves the summary DataFrame to the declared output path.
    """
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    logger.info(f"Successfully wrote summary to {OUTPUT_PATH}")
    logger.info(f"Output content:\n{df.to_string()}")

def main():
    """
    Main entry point for T022.
    """
    logger.info("Starting T022: Generate Summary CSV")
    try:
        # 1. Load data from T021
        df = load_aggregated_data()
        
        # 2. Generate summary
        summary_df = generate_summary(df)
        
        # 3. Save output
        save_summary(summary_df)
        
        logger.info("T022 completed successfully.")
        return 0
    except FileNotFoundError as e:
        logger.critical(f"Pipeline dependency missing: {e}")
        return 1
    except Exception as e:
        logger.critical(f"Unexpected error during T022: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())