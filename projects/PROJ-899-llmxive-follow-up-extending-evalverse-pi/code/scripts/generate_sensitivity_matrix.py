"""
Script to generate full sensitivity matrix.
"""
import os
import sys
import logging
import pandas as pd
from pathlib import Path
from src.models.evaluate import generate_full_sensitivity_matrix
from src.utils import get_logger, write_csv
from src.config import get_data_root

logger = get_logger(__name__)

def load_sensitivity_data() -> pd.DataFrame:
    """Load sensitivity sweep raw data."""
    path = os.path.join(get_data_root(), "sensitivity_sweep_raw.csv")
    if not os.path.exists(path):
        logger.error(f"Sensitivity sweep data not found: {path}")
        return pd.DataFrame()
    return pd.read_csv(path)

def generate_full_matrix(sweep_data: pd.DataFrame):
    """Generate full sensitivity matrix."""
    if sweep_data.empty:
        logger.warning("No sensitivity sweep data to process")
        return

    df = generate_full_sensitivity_matrix(sweep_data)
    logger.info(f"Generated sensitivity matrix with {len(df)} dimensions")

def main():
    """Main entry point."""
    try:
        sweep_data = load_sensitivity_data()
        generate_full_matrix(sweep_data)
        return 0
    except Exception as e:
        logger.error(f"Error generating sensitivity matrix: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
