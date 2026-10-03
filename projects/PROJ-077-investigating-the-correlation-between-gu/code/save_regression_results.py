"""
Script to save regression results (wrapper).
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from code.analysis import run_multivariate_regression, save_regression_results, load_processed_data
from code.logging_config import log_operation

def run_save_regression_pipeline() -> None:
    """Runs regression and saves results."""
    df = load_processed_data()
    res = run_multivariate_regression(df)
    save_regression_results(res)

def main():
    """Entry point."""
    try:
        run_save_regression_pipeline()
    except Exception as e:
        print(f"Regression pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
