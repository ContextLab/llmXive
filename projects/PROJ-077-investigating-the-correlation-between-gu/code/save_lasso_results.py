"""
Script to save Lasso results (wrapper).
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from code.analysis import run_lasso_regression, save_lasso_results, load_processed_data
from code.logging_config import log_operation

def run_save_lasso_pipeline() -> None:
    """Runs Lasso and saves results."""
    df = load_processed_data()
    res = run_lasso_regression(df)
    save_lasso_results(res)

def main():
    """Entry point."""
    try:
        run_save_lasso_pipeline()
    except Exception as e:
        print(f"Lasso pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
