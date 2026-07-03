"""
Data persistence module for synthetic data generation.

Handles saving generated synthetic datasets along with their metadata
(seed, configuration) to ensure reproducibility.
"""
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd

from simulation.config import SimulationConfig
from simulation.logger import setup_logger

# Ensure logger is available
logger = setup_logger(__name__)

# Ensure output directory exists
OUTPUT_DIR = Path("data/synthetic")

def _ensure_output_dir():
    """Create the output directory if it doesn't exist."""
    if not OUTPUT_DIR.exists():
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created output directory: {OUTPUT_DIR}")

def _generate_run_id() -> str:
    """Generate a unique run ID based on timestamp and random suffix."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = np.random.randint(1000, 9999)
    return f"{timestamp}_{suffix}"

def _serialize_config(config: SimulationConfig) -> Dict[str, Any]:
    """Convert SimulationConfig to a JSON-serializable dictionary."""
    # Handle dataclass conversion
    if hasattr(config, '__dataclass_fields__'):
        result = {}
        for field_name, field_obj in config.__dataclass_fields__.items():
            value = getattr(config, field_name)
            # Convert numpy types to native Python types
            if isinstance(value, np.ndarray):
                result[field_name] = value.tolist()
            elif isinstance(value, (np.integer, np.floating)):
                result[field_name] = value.item()
            elif isinstance(value, (list, tuple)):
                result[field_name] = [
                    v.item() if isinstance(v, (np.integer, np.floating)) else v 
                    for v in value
                ]
            else:
                result[field_name] = value
        return result
    return config if isinstance(config, dict) else {}

def save_synthetic_data(
    data: Dict[str, np.ndarray],
    config: SimulationConfig,
    seed: int,
    run_id: Optional[str] = None,
    metadata_extra: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save synthetic data and metadata to disk.
    
    Args:
        data: Dictionary mapping column names to numpy arrays.
        config: SimulationConfig instance used to generate the data.
        seed: Random seed used for generation.
        run_id: Optional unique identifier for this run. If None, generated automatically.
        metadata_extra: Optional additional metadata to include.
        
    Returns:
        Path to the saved CSV file (relative to project root).
        
    Raises:
        ValueError: If data is empty or config is invalid.
        IOError: If file cannot be written.
    """
    _ensure_output_dir()
    
    if not data:
        raise ValueError("Data dictionary cannot be empty")
        
    if run_id is None:
        run_id = _generate_run_id()
        
    # Prepare DataFrame
    df = pd.DataFrame(data)
    
    # Generate file paths
    csv_path = OUTPUT_DIR / f"data_{run_id}.csv"
    meta_path = OUTPUT_DIR / f"meta_{run_id}.json"
    
    # Serialize config
    config_dict = _serialize_config(config)
    
    # Build metadata
    metadata = {
        "run_id": run_id,
        "seed": seed,
        "generated_at": datetime.now().isoformat(),
        "config": config_dict,
        "data_shape": {
            "rows": len(df),
            "columns": len(df.columns)
        },
        "column_names": list(df.columns),
        "statistics": {
            col: {
                "mean": float(df[col].mean()),
                "std": float(df[col].std()),
                "min": float(df[col].min()),
                "max": float(df[col].max())
            }
            for col in df.columns
        }
    }
    
    # Add extra metadata if provided
    if metadata_extra:
        metadata.update(metadata_extra)
    
    try:
        # Save CSV
        df.to_csv(csv_path, index=False)
        logger.info(f"Saved synthetic data to: {csv_path}")
        
        # Save metadata
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        logger.info(f"Saved metadata to: {meta_path}")
        
        return str(csv_path)
        
    except IOError as e:
        logger.error(f"Failed to write files: {e}")
        raise
    
def load_synthetic_data(run_id: str) -> tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Load synthetic data and metadata by run_id.
    
    Args:
        run_id: The unique identifier of the run to load.
        
    Returns:
        Tuple of (DataFrame, metadata dictionary)
        
    Raises:
        FileNotFoundError: If files do not exist.
    """
    csv_path = OUTPUT_DIR / f"data_{run_id}.csv"
    meta_path = OUTPUT_DIR / f"meta_{run_id}.json"
    
    if not csv_path.exists():
        raise FileNotFoundError(f"Data file not found: {csv_path}")
    if not meta_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {meta_path}")
        
    df = pd.read_csv(csv_path)
    
    with open(meta_path, 'r') as f:
        metadata = json.load(f)
        
    logger.info(f"Loaded synthetic data: {csv_path}")
    return df, metadata

def list_available_runs() -> list[str]:
    """
    List all available synthetic data runs.
    
    Returns:
        List of run_ids found in the output directory.
    """
    if not OUTPUT_DIR.exists():
        return []
        
    runs = []
    for file in OUTPUT_DIR.glob("data_*.csv"):
        run_id = file.stem.replace("data_", "")
        runs.append(run_id)
    return sorted(runs)

def get_run_summary(run_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a summary of a specific run without loading the full data.
    
    Args:
        run_id: The unique identifier of the run.
        
    Returns:
        Metadata dictionary or None if not found.
    """
    meta_path = OUTPUT_DIR / f"meta_{run_id}.json"
    if not meta_path.exists():
        return None
        
    with open(meta_path, 'r') as f:
        return json.load(f)