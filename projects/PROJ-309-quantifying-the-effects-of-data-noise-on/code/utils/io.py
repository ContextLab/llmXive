import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union
import logging
import numpy as np
from code.utils.data_models import Trajectory

logger = logging.getLogger(__name__)

def export_csv(data: Union[np.ndarray, list], path: Union[str, Path], headers: Optional[list] = None):
    """Export data to CSV."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        if headers:
            writer.writerow(headers)
        if isinstance(data, np.ndarray):
            for row in data:
                writer.writerow(row)
        else:
            for row in data:
                writer.writerow(row)
    logger.info(f"Exported CSV to {path}")

def write_json_artifact(data: Dict[str, Any], path: Union[str, Path]):
    """Write a dictionary to a JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Written JSON artifact to {path}")

def compute_file_checksum(path: Union[str, Path]) -> str:
    """Compute MD5 checksum of a file."""
    path = Path(path)
    hash_md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def load_trajectory(path: Union[str, Path]) -> Trajectory:
    """
    Load a trajectory from a CSV file.
    Expected format: header row, then rows of floats.
    Assumes columns correspond to state dimensions.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Trajectory file not found: {path}")
    
    data = np.loadtxt(path, delimiter=',', skiprows=1)
    # Ensure 2D
    if data.ndim == 1:
        data = data.reshape(-1, 1)
        
    # Extract metadata if available in sidecar? 
    # For now, assume standard load.
    # Create a Trajectory object
    # We need to infer system_type and seed from filename or pass them?
    # The function signature in the prompt implies we just load data.
    # We'll create a basic Trajectory object.
    # The actual metadata (system, seed) should be passed or derived.
    # Let's assume the caller handles metadata or we store it in the object if possible.
    # Since Trajectory is a dataclass, we can add metadata fields if needed, 
    # but for now we just return the object with state.
    # To be safe, we return a Trajectory with state and empty metadata.
    return Trajectory(state=data, system_type="unknown", seed=0)
