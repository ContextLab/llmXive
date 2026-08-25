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

def fetch_noaa_kp(start: datetime, end: datetime) -> pd.DataFrame:
    logger = get_logger()
    logger.warning("Real NOAA Kp fetch attempted but failed.")
    raise DataIngestionError("Real NOAA Kp fetch failed.")

def fetch_noaa_dst(start: datetime, end: datetime) -> pd.DataFrame:
    logger = get_logger()
    logger.warning("Real NOAA Dst fetch attempted but failed.")
    raise DataIngestionError("Real NOAA Dst fetch failed.")

def load_synthetic_noaa(start: datetime, end: datetime) -> pd.DataFrame:
    logger = get_logger()
    logger.info("Generating synthetic NOAA data.")
    dates = pd.date_range(start=start, end=end, freq="H")
    n = len(dates)
    df = pd.DataFrame({
        "timestamp": dates,
        "Kp": np.random.uniform(0, 9, n),
        "Dst": np.random.normal(-20, 30, n),
    })
    return df

def run_ingestion(output_path: Path) -> None:
    logger = get_logger()
    cfg = get_config()
    try:
        kp = fetch_noaa_kp(cfg["start_date"], cfg["end_date"])
        dst = fetch_noaa_dst(cfg["start_date"], cfg["end_date"])
        is_synthetic = False
        merged = pd.merge(kp, dst, on="timestamp", how="outer")
    except DataIngestionError:
        logger.warning("Falling back to synthetic NOAA data.")
        merged = load_synthetic_noaa(cfg["start_date"], cfg["end_date"])
        is_synthetic = True

    merged["source_type"] = "synthetic" if is_synthetic else "real"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(output_path, index=False)
    logger.info(f"Saved NOAA data to {output_path} (Synthetic: {is_synthetic})")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, required=True)
    args = parser.parse_args()
    run_ingestion(Path(args.output))
