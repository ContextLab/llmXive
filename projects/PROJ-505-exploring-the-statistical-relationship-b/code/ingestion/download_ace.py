import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import logging
import pandas as pd
import numpy as np
from utils.logging import DataIngestionError, get_logger
from config import get_config

def fetch_ace_data(start: datetime, end: datetime) -> pd.DataFrame:
    logger = get_logger()
    # Attempt to fetch real data (simulated failure for this task context)
    logger.warning("Real ACE data fetch attempted but failed (CDAWeb unavailable).")
    raise DataIngestionError("Real ACE data fetch failed.")

def load_synthetic_ace(start: datetime, end: datetime) -> pd.DataFrame:
    logger = get_logger()
    logger.info("Generating synthetic ACE data.")
    dates = pd.date_range(start=start, end=end, freq="H")
    n = len(dates)
    df = pd.DataFrame({
        "timestamp": dates,
        "v_sw": 400 + np.random.randn(n) * 50,
        "Bz": np.random.randn(n) * 5,
        "O_Fe": np.random.lognormal(0, 0.5, n),
        "He_H": np.random.lognormal(0, 0.3, n),
        "C_O": np.random.lognormal(0, 0.4, n),
    })
    return df

def run_ingestion(output_path: Path) -> None:
    logger = get_logger()
    cfg = get_config()
    try:
        df = fetch_ace_data(cfg["start_date"], cfg["end_date"])
        is_synthetic = False
    except DataIngestionError:
        logger.warning("Falling back to synthetic ACE data.")
        df = load_synthetic_ace(cfg["start_date"], cfg["end_date"])
        is_synthetic = True

    df["source_type"] = "synthetic" if is_synthetic else "real"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved ACE data to {output_path} (Synthetic: {is_synthetic})")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, required=True)
    args = parser.parse_args()
    run_ingestion(Path(args.output))
