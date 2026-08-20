import os
import sys
import logging
from pathlib import Path
import pandas as pd
import json
from src.models.metrics import run_threshold_sweep
from src.utils import get_logger
from src.config import get_data_root

def load_dimension_results() -> pd.DataFrame:
    """Load dimension results from T016/T017."""
    # Assuming a file exists from previous steps
    path = os.path.join(get_data_root(), "dimension_metrics.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()

def main():
    """
    Run threshold sweep (T026).
    Generates data/sensitivity_sweep_raw.csv.
    """
    logger = get_logger(__name__)
    
    results = load_dimension_results()
    if results.empty:
        logger.warning("No dimension results found. Cannot run sweep.")
        return 1
    
    # Run the sweep
    sweep_df = run_threshold_sweep(results)
    
    logger.info(f"Generated sensitivity sweep with {len(sweep_df)} rows.")
    return 0

if __name__ == "__main__":
    sys.exit(main())