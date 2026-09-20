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

def load_correlation_results(filepath: str) -> pd.DataFrame:
    """Load correlation results from JSON."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Correlation results file not found: {filepath}")
    return pd.read_json(filepath)

def write_correlation_csv(df_results: pd.DataFrame, output_path: Path):
    """Write correlation results to CSV."""
    df_results.to_csv(output_path, index=False)
    logger.info(f"Wrote correlation results to {output_path}")

def validate_output(output_path: Path):
    """Validate that the output CSV exists and has the correct schema."""
    if not output_path.exists():
        raise FileNotFoundError(f"Output file not found: {output_path}")
    
    df = pd.read_csv(output_path)
    required_cols = {'taxon', 'coefficient', 'raw_pvalue', 'adj_pvalue'}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"Output CSV missing required columns. Found: {df.columns.tolist()}, Expected: {required_cols}")
    
    logger.info(f"Validation passed for {output_path}")

def run_correlation_csv_pipeline(input_dir: Path, output_dir: Path):
    """Run the pipeline to convert JSON results to CSV."""
    json_path = input_dir / "correlation_results.json"
    csv_path = output_dir / "correlation_results.csv"
    
    df = load_correlation_results(str(json_path))
    write_correlation_csv(df, csv_path)
    validate_output(csv_path)

def main():
    """Main entry point."""
    results_dir = get_results_path()
    run_correlation_csv_pipeline(results_dir, results_dir)

if __name__ == "__main__":
    main()
