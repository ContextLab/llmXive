"""Persistence utilities for simulation data and seed management."""
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union

import pandas as pd
import numpy as np

from simulation.logger import setup_logger
from simulation.schema import save_seed_config, compute_config_hash, load_seed_config, validate_seed_config

logger = setup_logger(__name__)

# Paths
SYNTHETIC_DATA_DIR = Path("data/synthetic")
SEED_CONFIG_PATH = Path("code/simulation/seed_config.json")

def ensure_data_directories() -> None:
    """Ensure all required data directories exist."""
    SYNTHETIC_DATA_DIR.mkdir(parents=True, exist_ok=True)

def save_synthetic_data(
    data: pd.DataFrame,
    config: Dict[str, Any],
    batch_id: str,
    seed: int,
    ground_truth_label: str
) -> str:
    """
    Save synthetic data to a Parquet file with metadata.
    
    Args:
        data: The generated data DataFrame
        config: The configuration used for generation
        batch_id: The batch identifier
        seed: The random seed used
        ground_truth_label: 'null' or 'alternative'
        
    Returns:
        Path to the saved file
    """
    ensure_data_directories()

    # Create filename
    filename = f"batch_{batch_id}_{seed}.parquet"
    filepath = SYNTHETIC_DATA_DIR / filename

    # Prepare metadata
    metadata = {
        "seed": seed,
        "config_json": json.dumps(config, default=str),
        "ground_truth_label": ground_truth_label
    }

    # Add metadata to DataFrame
    for key, value in metadata.items():
        data[key] = value

    # Save to Parquet
    data.to_parquet(filepath, index=False)
    logger.log("save_synthetic_data", file=str(filepath), rows=len(data))

    return str(filepath)

def load_synthetic_data(filepath: Union[str, Path]) -> pd.DataFrame:
    """
    Load synthetic data from a Parquet file.
    
    Args:
        filepath: Path to the Parquet file
        
    Returns:
        The loaded DataFrame
        
    Raises:
        FileNotFoundError: If the file doesn't exist
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Synthetic data file not found: {filepath}")

    return pd.read_parquet(filepath)

def list_available_runs() -> list:
    """
    List all available synthetic data runs.
    
    Returns:
        List of dictionaries with run metadata
    """
    if not SYNTHETIC_DATA_DIR.exists():
        return []

    runs = []
    for filepath in SYNTHETIC_DATA_DIR.glob("batch_*.parquet"):
        try:
            df = load_synthetic_data(filepath)
            runs.append({
                "file": filepath.name,
                "batch_id": filepath.stem.split("_")[1],
                "seed": int(df["seed"].iloc[0]) if "seed" in df.columns else None,
                "ground_truth_label": df["ground_truth_label"].iloc[0] if "ground_truth_label" in df.columns else None,
                "rows": len(df)
            })
        except Exception as e:
            logger.log("list_available_runs_error", file=str(filepath), error=str(e))

    return runs

def get_run_summary(batch_id: str, seed: int) -> Optional[Dict[str, Any]]:
    """
    Get summary information for a specific run.
    
    Args:
        batch_id: The batch identifier
        seed: The random seed
        
    Returns:
        Dictionary with run summary or None if not found
    """
    filename = f"batch_{batch_id}_{seed}.parquet"
    filepath = SYNTHETIC_DATA_DIR / filename

    if not filepath.exists():
        return None

    df = load_synthetic_data(filepath)
    return {
        "file": filename,
        "batch_id": batch_id,
        "seed": seed,
        "rows": len(df),
        "columns": list(df.columns),
        "ground_truth_label": df["ground_truth_label"].iloc[0] if "ground_truth_label" in df.columns else None
    }

def save_seed_config_entry(batch_id: str, config: Dict[str, Any]) -> str:
    """
    Save a seed configuration entry for a batch.
    
    Args:
        batch_id: The batch identifier
        config: The configuration dictionary
        
    Returns:
        The seed used for this batch
    """
    import random
    
    # Generate a random seed
    seed = random.randint(0, 2**32 - 1)
    
    # Compute config hash
    config_hash = compute_config_hash(config)
    
    # Save to seed config file
    save_seed_config(batch_id, seed, config_hash)
    
    logger.log("save_seed_config_entry", batch_id=batch_id, seed=seed)
    
    return str(seed)

def load_seed_config_entry(batch_id: str) -> Optional[Dict[str, Any]]:
    """
    Load the seed configuration for a specific batch.
    
    Args:
        batch_id: The batch identifier
        
    Returns:
        Dictionary with seed config or None if not found
    """
    config = load_seed_config()
    if batch_id in config:
        return config[batch_id]
    return None

def validate_seed_config_file() -> bool:
    """
    Validate the seed configuration file.
    
    Returns:
        True if valid, False otherwise
    """
    config = load_seed_config()
    return validate_seed_config(config)
