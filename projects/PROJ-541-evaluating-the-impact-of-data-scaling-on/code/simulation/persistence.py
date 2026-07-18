"""
Persistence module for synthetic data.
Handles saving and loading synthetic datasets with metadata for reproducibility.
"""
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union
import numpy as np
import pandas as pd
from simulation.config import SimulationConfig
from simulation.logger import setup_logger

logger = setup_logger(__name__)

# Base directory for synthetic data
SYNTHETIC_DATA_DIR = Path("data/synthetic")

def _ensure_directory():
    """Ensure the synthetic data directory exists."""
    SYNTHETIC_DATA_DIR.mkdir(parents=True, exist_ok=True)

def _serialize_config(config: SimulationConfig) -> Dict[str, Any]:
    """
    Serialize SimulationConfig to a JSON-serializable dictionary.
    Handles numpy types and complex objects.
    """
    config_dict = {}
    for field_name, field_value in config.__dict__.items():
        if isinstance(field_value, (str, int, float, bool, type(None))):
            config_dict[field_name] = field_value
        elif isinstance(field_value, np.integer):
            config_dict[field_name] = int(field_value)
        elif isinstance(field_value, np.floating):
            config_dict[field_name] = float(field_value)
        elif isinstance(field_value, np.ndarray):
            config_dict[field_name] = field_value.tolist()
        elif isinstance(field_value, list):
            config_dict[field_name] = [
                int(x) if isinstance(x, np.integer) else
                float(x) if isinstance(x, np.floating) else
                x.tolist() if isinstance(x, np.ndarray) else
                x for x in field_value
            ]
        elif isinstance(field_value, dict):
            config_dict[field_name] = {
                k: (int(v) if isinstance(v, np.integer) else
                    float(v) if isinstance(v, np.floating) else
                    v.tolist() if isinstance(v, np.ndarray) else
                    v)
                for k, v in field_value.items()
            }
        else:
            config_dict[field_name] = str(field_value)
    return config_dict

def _serialize_data(data: Dict[str, np.ndarray]) -> Dict[str, Any]:
    """
    Serialize numpy arrays in data dictionary to lists for JSON.
    """
    serialized = {}
    for key, value in data.items():
        if isinstance(value, np.ndarray):
            serialized[key] = value.tolist()
        elif isinstance(value, pd.DataFrame):
            serialized[key] = value.to_dict(orient='list')
        else:
            serialized[key] = value
    return serialized

def save_synthetic_data(
    data: Dict[str, np.ndarray],
    config: SimulationConfig,
    seed: int,
    run_id: Optional[str] = None,
    extra_metadata: Optional[Dict[str, Any]] = None
) -> Tuple[str, str]:
    """
    Save synthetic data and metadata to disk.

    Args:
        data: Dictionary of numpy arrays (e.g., {'group_a': ..., 'group_b': ...})
        config: SimulationConfig instance used to generate the data
        seed: Random seed used for generation
        run_id: Optional unique identifier for this run. If None, generated from timestamp.
        extra_metadata: Optional additional metadata to include

    Returns:
        Tuple of (data_file_path, metadata_file_path) as strings

    Raises:
        ValueError: If data is empty
        IOError: If writing fails
    """
    if not data:
        raise ValueError("Cannot save empty data dictionary")

    _ensure_directory()

    if run_id is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_id = f"run_{timestamp}"

    # Create run directory
    run_dir = SYNTHETIC_DATA_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # Prepare metadata
    metadata = {
        "run_id": run_id,
        "seed": seed,
        "generated_at": datetime.now().isoformat(),
        "config": _serialize_config(config),
        "data_shape": {k: v.shape if hasattr(v, 'shape') else len(v) for k, v in data.items()},
        "data_types": {k: str(type(v)) for k, v in data.items()}
    }

    if extra_metadata:
        metadata.update(extra_metadata)

    # Save metadata
    metadata_path = run_dir / "metadata.json"
    try:
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Saved metadata to {metadata_path}")
    except IOError as e:
        logger.error(f"Failed to write metadata: {e}")
        raise

    # Save data as CSV files for each array
    data_paths = {}
    for key, value in data.items():
        if isinstance(value, np.ndarray):
            # Convert to DataFrame for CSV saving
            if value.ndim == 1:
                df = pd.DataFrame({key: value})
            elif value.ndim == 2:
                df = pd.DataFrame(value, columns=[f"{key}_col_{i}" for i in range(value.shape[1])])
            else:
                # Flatten higher dimensions
                df = pd.DataFrame({f"{key}_flat": value.flatten()})

            file_name = f"{key}.csv"
            file_path = run_dir / file_name
            df.to_csv(file_path, index=False)
            data_paths[key] = str(file_path)
            logger.debug(f"Saved data for '{key}' to {file_path}")

    # Save summary index
    index_path = SYNTHETIC_DATA_DIR / "index.json"
    try:
        # Load existing index or create new
        if index_path.exists():
            with open(index_path, 'r') as f:
                index = json.load(f)
        else:
            index = []

        index.append({
            "run_id": run_id,
            "seed": seed,
            "timestamp": metadata["generated_at"],
            "config_summary": {
                "distribution": config.distribution_type,
                "sample_size": config.sample_size,
                "mean_diff": config.mean_diff
            },
            "files": list(data_paths.keys())
        })

        with open(index_path, 'w') as f:
            json.dump(index, f, indent=2)
        logger.info(f"Updated index at {index_path}")
    except IOError as e:
        logger.warning(f"Failed to update index: {e}")

    return str(metadata_path), str(run_dir)

def load_synthetic_data(run_id: str) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
    """
    Load synthetic data and metadata for a specific run.

    Args:
        run_id: The run identifier (directory name under data/synthetic/)

    Returns:
        Tuple of (data_dict, metadata_dict)

    Raises:
        FileNotFoundError: If the run directory or metadata file doesn't exist
        ValueError: If data cannot be loaded
    """
    run_dir = SYNTHETIC_DATA_DIR / run_id

    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory not found: {run_dir}")

    metadata_path = run_dir / "metadata.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found for run {run_id}")

    # Load metadata
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)

    # Load data files
    data = {}
    data_info = metadata.get("data_shape", {})

    for key in data_info.keys():
        file_path = run_dir / f"{key}.csv"
        if not file_path.exists():
            raise FileNotFoundError(f"Data file not found for key '{key}': {file_path}")

        df = pd.read_csv(file_path)
        # Convert back to numpy array
        if len(df.columns) == 1:
            data[key] = df.iloc[:, 0].values
        else:
            data[key] = df.values

    logger.info(f"Loaded data for run {run_id} from {run_dir}")
    return data, metadata

def list_available_runs() -> list:
    """
    List all available synthetic data runs.

    Returns:
        List of run_ids (directory names)
    """
    if not SYNTHETIC_DATA_DIR.exists():
        return []

    runs = []
    for item in SYNTHETIC_DATA_DIR.iterdir():
        if item.is_dir() and item.name != "__pycache__":
            # Check if it has metadata
            if (item / "metadata.json").exists():
                runs.append(item.name)

    return sorted(runs)

def get_run_summary(run_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a summary of a specific run without loading all data.

    Args:
        run_id: The run identifier

    Returns:
        Dictionary with run summary or None if not found
    """
    run_dir = SYNTHETIC_DATA_DIR / run_id

    if not run_dir.exists():
        return None

    metadata_path = run_dir / "metadata.json"
    if not metadata_path.exists():
        return None

    with open(metadata_path, 'r') as f:
        metadata = json.load(f)

    # Return a summary (exclude large data shapes if needed)
    summary = {
        "run_id": metadata.get("run_id"),
        "seed": metadata.get("seed"),
        "generated_at": metadata.get("generated_at"),
        "config": metadata.get("config"),
        "data_shape": metadata.get("data_shape"),
        "data_types": metadata.get("data_types")
    }

    return summary
