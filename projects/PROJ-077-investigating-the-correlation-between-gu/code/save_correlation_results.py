"""
Script to save correlation results (wrapper).
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

from code.analysis import compute_spearman_correlation, save_correlation_results, load_processed_data
from code.logging_config import log_operation

def run_save_correlation_pipeline() -> None:
    """Runs correlation and saves results."""
    df = load_processed_data()
    r, p = compute_spearman_correlation(df)
    n = df[["shannon_index", "fluid_intelligence_score"]].dropna().shape[0]
    save_correlation_results(r, p, n)

def main():
    """Entry point."""
    try:
        run_save_correlation_pipeline()
    except Exception as e:
        print(f"Correlation pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
