"""Persistence utilities for simulation data and seeds."""
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union
import pandas as pd
from simulation.logger import setup_logger
from simulation.schema import save_seed_config

logger = setup_logger("persistence")

def save_synthetic_data(
    data: pd.DataFrame,
    config: Dict[str, Any],
    batch_id: str,
    seed: int,
    ground_truth_label: str,
    output_dir: str = "data/synthetic"
) -> str:
    """
    Save synthetic data batch to parquet with metadata.
    Returns the path to the saved file.
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = f"batch_{batch_id}_{seed}.parquet"
    filepath = os.path.join(output_dir, filename)

    # Add metadata columns
    data["seed"] = seed
    data["config_json"] = json.dumps(config)
    data["ground_truth_label"] = ground_truth_label

    data.to_parquet(filepath, index=False)
    logger.log_operation("save_synthetic_data", filepath=filepath, batch_id=batch_id, seed=seed)
    return filepath

def load_synthetic_data(filepath: str) -> pd.DataFrame:
    """Load synthetic data from parquet file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Synthetic data file not found: {filepath}")
    return pd.read_parquet(filepath)

def list_available_runs(data_dir: str = "data/synthetic") -> list:
    """List all available synthetic data runs."""
    runs = []
    if os.path.exists(data_dir):
        for f in os.listdir(data_dir):
            if f.endswith(".parquet"):
                runs.append(os.path.join(data_dir, f))
    return runs

def get_run_summary(filepath: str) -> Dict[str, Any]:
    """Get summary of a run without loading full data."""
    df = load_synthetic_data(filepath)
    return {
        "file": filepath,
        "rows": len(df),
        "columns": list(df.columns),
        "seed": df["seed"].iloc[0] if "seed" in df.columns else None,
        "ground_truth": df["ground_truth_label"].iloc[0] if "ground_truth_label" in df.columns else None
    }

def save_seed_config_entry(
    batch_id: str,
    seed: int,
    config_hash: str,
    timestamp: Optional[str] = None,
    config_path: str = "data/config/seed_config.json"
) -> None:
    """
    Append a new batch's seed to the seed_config.json file.
    Implements the append-only policy: new batches add new keys, existing keys are never overwritten.
    """
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat()

    new_entry = {
        batch_id: {
            "seed": seed,
            "timestamp": timestamp,
            "config_hash": config_hash
        }
    }

    save_seed_config(new_entry, config_path)
    logger.log_operation("save_seed_config_entry", batch_id=batch_id, seed=seed)
