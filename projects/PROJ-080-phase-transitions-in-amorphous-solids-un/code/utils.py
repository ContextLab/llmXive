import os
import json
from typing import Any, Dict, Iterator, Optional, Tuple, Union
import numpy as np
import h5py
import pandas as pd

# Constitution Principle VII: Fixed seed for reproducibility
SEED = 42

def set_seed(seed: int = SEED):
    """Set global random seeds for reproducibility."""
    np.random.seed(seed)
    # If using torch or other libraries, set their seeds here too
    # import torch
    # torch.manual_seed(seed)


def stream_hdf5(path: str, chunk_size: int = 1000) -> Iterator[pd.DataFrame]:
    """
    Stream data from an HDF5 file in chunks to manage memory.

    Args:
        path: Path to the HDF5 file.
        chunk_size: Number of rows to read per chunk.

    Yields:
        Pandas DataFrames containing chunks of data.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"HDF5 file not found: {path}")

    with h5py.File(path, 'r') as f:
        # Assuming the data is in a dataset named 'data' or similar
        # We need to be flexible or assume a standard structure
        # Let's assume the root contains a dataset 'particles' or 'data'
        key = list(f.keys())[0] if len(f.keys()) > 0 else None
        if key is None:
            raise ValueError("HDF5 file is empty or has no datasets.")
        
        ds = f[key]
        total_rows = ds.shape[0]
        
        for start in range(0, total_rows, chunk_size):
            end = min(start + chunk_size, total_rows)
            chunk_data = ds[start:end]
            # Convert to DataFrame if possible, assuming structured array or 2D array
            if isinstance(chunk_data, np.ndarray) and len(chunk_data.shape) == 1:
                # Try to infer columns if it's a structured array
                if chunk_data.dtype.names:
                    df = pd.DataFrame(chunk_data)
                else:
                    # Fallback: create generic columns
                    df = pd.DataFrame({'value': chunk_data})
            else:
                df = pd.DataFrame(chunk_data)
            yield df


def stream_parquet(path: str, chunk_size: int = 1000) -> Iterator[pd.DataFrame]:
    """
    Stream data from a Parquet file in chunks.

    Args:
        path: Path to the Parquet file.
        chunk_size: Number of rows to read per chunk.

    Yields:
        Pandas DataFrames containing chunks of data.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Parquet file not found: {path}")

    # Pandas read_parquet doesn't natively support row-based streaming in one call
    # without pyarrow's dataset API. Using pyarrow for chunking.
    try:
        import pyarrow.parquet as pq
    except ImportError:
        raise ImportError("pyarrow is required for streaming parquet files.")

    parquet_file = pq.ParquetFile(path)
    
    for batch in parquet_file.iter_batches(batch_size=chunk_size):
        yield batch.to_pandas()


def validate_particle_count(df: pd.DataFrame, max_count: int = 100000):
    """
    Validate that the particle count does not exceed the limit (FR-006).

    Args:
        df: DataFrame containing particle data.
        max_count: Maximum allowed number of particles.

    Raises:
        ValueError: If particle count exceeds max_count.
    """
    count = len(df)
    if count > max_count:
        raise ValueError(f"Particle count ({count}) exceeds limit ({max_count}). "
                         "This violates FR-006. Please use a smaller dataset or stream.")


def save_json_output(data: Dict, path: str):
    """
    Save a dictionary to a JSON file.

    Args:
        data: Dictionary to save.
        path: Output file path.
    """
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
