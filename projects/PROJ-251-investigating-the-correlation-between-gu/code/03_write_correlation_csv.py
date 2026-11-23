import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd

from utils.config import get_results_path
from utils.logging_config import get_logger

logger = get_logger(__name__)

def load_correlation_results() -> pd.DataFrame:
    """Load the correlation results from JSON."""
    path = get_results_path() / "correlation_results.json"
    if not path.exists():
        raise FileNotFoundError(f"Correlation results not found at {path}. "
                                "Ensure T032 has completed.")
    return pd.read_json(path)

def write_correlation_csv(df: pd.DataFrame):
    """Write results to CSV."""
    output_path = get_results_path() / "correlation_results.csv"
    
    # Ensure columns are in correct order
    cols = ['taxon', 'coefficient', 'raw_pvalue', 'adj_pvalue']
    if not all(c in df.columns for c in cols):
        raise ValueError(f"Expected columns {cols} not found in results.")
        
    df[cols].to_csv(output_path, index=False)
    logger.info(f"Wrote correlation results to {output_path}")

def validate_output():
    """Basic validation of the output CSV."""
    path = get_results_path() / "correlation_results.csv"
    if not path.exists():
        raise FileNotFoundError("Output CSV not found.")
    
    df = pd.read_csv(path)
    required = ['taxon', 'coefficient', 'raw_pvalue', 'adj_pvalue']
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Check for NaNs in numeric columns
    if df['coefficient'].isna().any() or df['raw_pvalue'].isna().any():
        logger.warning("NaN values found in coefficient or raw_pvalue.")
        
    logger.info("Validation passed.")

def run_correlation_csv_pipeline():
    """Main pipeline for writing CSV."""
    logger.info("Starting Correlation CSV generation.")
    df = load_correlation_results()
    write_correlation_csv(df)
    validate_output()
    logger.info("Correlation CSV generation completed.")

def main():
    run_correlation_csv_pipeline()

if __name__ == "__main__":
    main()
