"""
validate_splits.py

Verifies the disjoint nature of the train, holdout, and novel sets,
and validates their existence/non-existence against the local proxy (AFLOW snapshot).

Dependencies:
  - data/processed/heas_train.csv
  - data/processed/holdout_known.csv
  - data/processed/true_novel.csv
  - data/raw/aflow_raw.parquet (Local Proxy)
"""
import logging
import sys
from pathlib import Path
from typing import Set

import pandas as pd

from config import DATA_PROCESSED, DATA_RAW, setup_logging
from api_client import query_local_proxy

# Setup logging for this script
logger = setup_logging()
logger.setLevel(logging.INFO)

def load_composition_set(csv_path: Path, column_name: str = "composition_string") -> Set[str]:
    """Loads a CSV and returns a set of composition strings."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Required file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    if column_name not in df.columns:
        raise ValueError(f"Column '{column_name}' not found in {csv_path}. Available: {df.columns.tolist()}")
    
    # Convert to set of strings to ensure uniqueness and type safety
    return set(df[column_name].astype(str).str.strip())

def main():
    logger.info("Starting split validation...")
    
    # Define paths
    train_path = DATA_PROCESSED / "heas_train.csv"
    holdout_path = DATA_PROCESSED / "holdout_known.csv"
    novel_path = DATA_PROCESSED / "true_novel.csv"
    
    # Load sets
    try:
        train_set = load_composition_set(train_path)
        holdout_set = load_composition_set(holdout_path)
        novel_set = load_composition_set(novel_path)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load dataset splits: {e}")
        sys.exit(1)

    logger.info(f"Loaded Train: {len(train_set)}, Holdout: {len(holdout_set)}, Novel: {len(novel_set)}")

    # 1. Verify Disjoint Sets
    logger.info("Verifying disjoint sets...")
    
    train_holdout_overlap = train_set & holdout_set
    if train_holdout_overlap:
        logger.error(f"FAIL: Train and Holdout overlap detected. Count: {len(train_holdout_overlap)}")
        sys.exit(1)
    
    train_novel_overlap = train_set & novel_set
    if train_novel_overlap:
        logger.error(f"FAIL: Train and Novel overlap detected. Count: {len(train_novel_overlap)}")
        sys.exit(1)
    
    holdout_novel_overlap = holdout_set & novel_set
    if holdout_novel_overlap:
        logger.error(f"FAIL: Holdout and Novel overlap detected. Count: {len(holdout_novel_overlap)}")
        sys.exit(1)
    
    logger.info("PASS: All sets are disjoint.")

    # 2. Verify Holdout Existence in Local Proxy
    logger.info("Verifying Holdout existence in Local Proxy...")
    holdout_missing = []
    
    # We assume the proxy is already loaded/indexed by query_local_proxy logic,
    # or we load it efficiently if the function does caching.
    # To be safe and efficient, we iterate. If the proxy implementation is slow,
    # we rely on its internal caching (as per T017c design).
    
    for comp in holdout_set:
        result = query_local_proxy(comp)
        if result.get("status") != "Found":
            holdout_missing.append(comp)
    
    if holdout_missing:
        logger.error(f"FAIL: {len(holdout_missing)} holdout compositions NOT found in Local Proxy.")
        sys.exit(1)
    
    logger.info(f"PASS: All {len(holdout_set)} holdout compositions found in Local Proxy.")

    # 3. Verify Novel Non-Existence in Local Proxy
    logger.info("Verifying Novel non-existence in Local Proxy...")
    novel_found = []
    
    for comp in novel_set:
        result = query_local_proxy(comp)
        if result.get("status") == "Found":
            novel_found.append(comp)
    
    if novel_found:
        logger.error(f"FAIL: {len(novel_found)} novel compositions were found in Local Proxy (should be novel).")
        sys.exit(1)
    
    logger.info(f"PASS: All {len(novel_set)} novel compositions correctly NOT found in Local Proxy.")

    logger.info("SUCCESS: All validations passed.")
    sys.exit(0)

if __name__ == "__main__":
    main()