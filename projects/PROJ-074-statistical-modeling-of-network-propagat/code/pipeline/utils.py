import hashlib
import json
import logging
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# --- Logging Setup ---
def setup_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """Set up a logger with optional file output."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger

# --- Seed Management ---
def set_global_seed(seed: int) -> None:
    """Pin random seeds for reproducibility."""
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

# --- Checksum Utility ---
def compute_checksum(path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

# --- Timestamp Normalization ---
def normalize_timestamp(ts: Any) -> datetime:
    """Normalize a timestamp string/object to a UTC datetime."""
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc)
    
    if isinstance(ts, str):
        # Attempt common formats
        formats = [
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(ts, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except ValueError:
                continue
        raise ValueError(f"Unable to parse timestamp: {ts}")
    
    raise TypeError(f"Unsupported timestamp type: {type(ts)}")

# --- Cascade Loading with Node Limit Enforcement (T014) ---
def load_cascade(
    file_path: str,
    node_limit: int = 2000,
    logger: Optional[logging.Logger] = None,
    skipped_log_path: Optional[str] = None
) -> Optional[pd.DataFrame]:
    """
    Load a cascade from a JSON edge-list file.
    
    Validates required columns, normalizes timestamps to UTC, and enforces
    the node limit. Oversized cascades are skipped and logged.
    
    Args:
        file_path: Path to the JSON file containing the cascade.
        node_limit: Maximum allowed number of nodes (default 2000).
        logger: Logger instance. If None, a default logger is created.
        skipped_log_path: Path to the log file for skipped cascades.
    
    Returns:
        A pandas DataFrame with the cascade data if valid and within limits,
        otherwise None.
    """
    if logger is None:
        logger = setup_logger("cascade_loader")
    
    path = Path(file_path)
    if not path.exists():
        logger.error(f"File not found: {file_path}")
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return None

    # Validate structure: expects a list of nodes or a dict with a 'nodes' key
    if isinstance(data, dict):
        if "nodes" not in data:
            logger.error(f"Missing 'nodes' key in {file_path}")
            return None
        nodes = data["nodes"]
    elif isinstance(data, list):
        nodes = data
    else:
        logger.error(f"Unexpected JSON structure in {file_path}")
        return None

    if not nodes:
        logger.warning(f"Empty cascade in {file_path}")
        return None

    # Convert to DataFrame
    try:
        df = pd.DataFrame(nodes)
    except Exception as e:
        logger.error(f"Failed to convert nodes to DataFrame in {file_path}: {e}")
        return None

    # Validate required columns
    required_cols = {"node_id", "timestamp", "cascade_id"}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        logger.error(f"Missing required columns in {file_path}: {missing_cols}")
        return None

    # Normalize timestamps
    try:
        df["timestamp"] = df["timestamp"].apply(normalize_timestamp)
    except ValueError as e:
        logger.error(f"Timestamp normalization failed in {file_path}: {e}")
        return None

    # T014: Enforce node limit
    num_nodes = len(df)
    cascade_id = df["cascade_id"].iloc[0] if not df["cascade_id"].empty else "unknown"

    if num_nodes > node_limit:
        msg = f"Cascade {cascade_id} exceeds node limit ({num_nodes} > {node_limit}). Skipping."
        logger.warning(msg)
        
        if skipped_log_path:
            log_path = Path(skipped_log_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write(f"{file_path}|{cascade_id}|{num_nodes}\n")
        
        return None

    return df

def validate_all_cascades(
    data_dir: str,
    node_limit: int = 2000,
    skipped_log_path: str = "skipped_cascades.log"
) -> Tuple[List[pd.DataFrame], int]:
    """
    Load and validate all JSON cascade files in a directory.
    
    Returns:
        A tuple of (list of valid DataFrames, count of skipped files).
    """
    logger = setup_logger("validator")
    data_path = Path(data_dir)
    if not data_path.exists():
        logger.error(f"Data directory not found: {data_dir}")
        return [], 0

    valid_cascades = []
    skipped_count = 0

    for json_file in data_path.glob("*.json"):
        logger.info(f"Processing {json_file.name}")
        df = load_cascade(
            str(json_file),
            node_limit=node_limit,
            logger=logger,
            skipped_log_path=skipped_log_path
        )
        if df is not None:
            valid_cascades.append(df)
        else:
            skipped_count += 1

    return valid_cascades, skipped_count

def validate_features(df: pd.DataFrame) -> bool:
    """
    Validate that the features DataFrame has no missing values.
    
    Args:
        df: The features DataFrame.
    
    Returns:
        True if valid, False otherwise.
    """
    if df.isnull().any().any():
        return False
    return True

def main():
    """CLI entry point for utils module (example usage)."""
    import argparse
    parser = argparse.ArgumentParser(description="Pipeline utilities CLI")
    parser.add_argument("--seed", type=int, default=12345, help="Random seed")
    parser.add_argument("--log-file", type=str, help="Log file path")
    args = parser.parse_args()

    set_global_seed(args.seed)
    logger = setup_logger("utils_cli", log_file=args.log_file)
    logger.info("Utils CLI started")

    if __name__ == "__main__":
        main()