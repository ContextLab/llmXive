import os
import json
from typing import Any, Dict, Iterator, Optional, Tuple, Union
import numpy as np
import h5py
import pandas as pd
import random

SEED = 42

def set_seed(seed: int = SEED) -> None:
    """Sets the global random seed for reproducibility."""
    np.random.seed(seed)
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def stream_hdf5(file_path: Union[str, Path], group: str = 'frames') -> Iterator[Dict[str, np.ndarray]]:
    """
    Streams data from an HDF5 file group.
    
    Args:
        file_path: Path to the HDF5 file.
        group: The group name to stream from.
        
    Yields:
        Dictionary of arrays for each item in the group.
    """
    with h5py.File(file_path, 'r') as f:
        if group not in f:
            return
        grp = f[group]
        for key in grp.keys():
            item = {}
            for sub_key in grp[key].keys():
                item[sub_key] = np.array(grp[key][sub_key])
            yield item

def stream_parquet(file_path: Union[str, Path]) -> Iterator[pd.DataFrame]:
    """
    Streams data from a Parquet file.
    
    Args:
        file_path: Path to the Parquet file.
        
    Yields:
        DataFrame chunks.
    """
    # Parquet streaming is chunk-based
    for chunk in pd.read_parquet(file_path, chunksize=1000):
        yield chunk

def validate_particle_count(frame_data: Dict[str, np.ndarray], max_count: int = 100_000) -> bool:
    """
    Validates that the particle count in a frame does not exceed the limit.
    
    Args:
        frame_data: Dictionary containing 'particle_count'.
        max_count: Maximum allowed particle count.
        
    Returns:
        True if valid, raises ValueError otherwise.
    """
    count = frame_data.get('particle_count', 0)
    if isinstance(count, np.ndarray):
        count = count[0] if count.size > 0 else 0
    
    if count > max_count:
        raise ValueError(f"Particle count {count} exceeds limit {max_count}.")
    return True

def save_json_output(data: Any, file_path: Union[str, Path]) -> None:
    """Saves data to a JSON file."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
