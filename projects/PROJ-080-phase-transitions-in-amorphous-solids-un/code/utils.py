import os
import json
from typing import Any, Dict, Iterator, Optional, Tuple, Union
import numpy as np
import h5py
import pandas as pd
from pathlib import Path

SEED = 42

def set_seed(seed: int = SEED) -> None:
    """Set random seed for numerical determinism."""
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def stream_hdf5(filepath: Union[str, Path], dataset_name: str) -> Iterator[np.ndarray]:
    """
    Stream data from an HDF5 file in chunks.
    
    Args:
        filepath: Path to HDF5 file
        dataset_name: Name of dataset to stream
    
    Yields:
        Chunks of data from the dataset
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"HDF5 file not found: {filepath}")
    
    with h5py.File(filepath, 'r') as f:
        dataset = f[dataset_name]
        chunk_size = min(1000, dataset.shape[0])
        
        for i in range(0, dataset.shape[0], chunk_size):
            end = min(i + chunk_size, dataset.shape[0])
            yield dataset[i:end]

def stream_parquet(filepath: Union[str, Path], chunksize: int = 1000) -> Iterator[pd.DataFrame]:
    """
    Stream data from a Parquet file in chunks.
    
    Args:
        filepath: Path to Parquet file
        chunksize: Number of rows per chunk
    
    Yields:
        Chunks of DataFrame
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Parquet file not found: {filepath}")
    
    for chunk in pd.read_parquet(filepath, chunksize=chunksize):
        yield chunk

def validate_particle_count(count: int, max_limit: int = 100000) -> None:
    """
    Validate particle count against maximum limit.
    
    Args:
        count: Number of particles
        max_limit: Maximum allowed particles
    
    Raises:
        ValueError: If particle count exceeds limit
    """
    if count > max_limit:
        raise ValueError(f"Particle count {count} exceeds maximum limit {max_limit}. "
                       "This dataset is too large for processing. Please use a smaller subset.")

def save_json_output(data: Dict, filepath: Union[str, Path]) -> None:
    """
    Save dictionary to JSON file.
    
    Args:
        data: Dictionary to save
        filepath: Path to output file
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
