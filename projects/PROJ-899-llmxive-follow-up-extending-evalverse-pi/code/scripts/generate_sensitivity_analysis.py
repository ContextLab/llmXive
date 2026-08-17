"""
Script to generate sensitivity analysis from threshold sweep data.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd
from src.models.evaluate import calculate_stability_and_flip_rate
from src.utils import get_logger
from src.config import get_data_root

logger = get_logger(__name__)

def load_sensitivity_data() -> pd.DataFrame:
    """Load sensitivity sweep raw data."""
    path = os.path.join(get_data_root(), "sensitivity_sweep_raw.csv")
    if not os.path.exists(path):
        logger.error(f"Sensitivity sweep data not found: {path}")
        return pd.DataFrame()
    return pd.read_csv(path)

def generate_analysis(sweep_data: pd.DataFrame):
    """Generate sensitivity analysis."""
    if sweep_data.empty:
        logger.warning("No sensitivity sweep data to analyze")
        return

    df = calculate_stability_and_flip_rate(sweep_data)
    logger.info(f"Generated sensitivity analysis with {len(df)} rows")

def main():
    """Main entry point."""
    try:
        sweep_data = load_sensitivity_data()
        generate_analysis(sweep_data)
        return 0
    except Exception as e:
        logger.error(f"Error in sensitivity analysis: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
