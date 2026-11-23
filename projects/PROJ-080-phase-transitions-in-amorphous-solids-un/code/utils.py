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
    
    This function satisfies FR-006 by ensuring memory usage stays within 
    acceptable limits for large files through chunked reading.

    Args:
        path: Path to the HDF5 file.
        chunk_size: Number of rows to read per chunk.

    Yields:
        Pandas DataFrames containing chunks of data.
    
    Raises:
        FileNotFoundError: If the HDF5 file does not exist.
        ValueError: If the HDF5 file is empty or has no datasets.
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
    
    This function satisfies FR-006 by ensuring memory usage stays within 
    acceptable limits for large files through chunked reading.

    Args:
        path: Path to the Parquet file.
        chunk_size: Number of rows to read per chunk.

    Yields:
        Pandas DataFrames containing chunks of data.
    
    Raises:
        FileNotFoundError: If the Parquet file does not exist.
        ImportError: If pyarrow is not installed.
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
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def verify_data(path: str, file_type: str = 'hdf5') -> bool:
    """
    Verify the existence and basic integrity of a data file.

    Args:
        path: Path to the data file.
        file_type: Type of file ('hdf5' or 'parquet').

    Returns:
        True if the file exists and is readable.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file type is unsupported or the file is corrupted.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Data file not found: {path}")
    
    if file_type == 'hdf5':
        try:
            with h5py.File(path, 'r') as f:
                if len(f.keys()) == 0:
                    raise ValueError("HDF5 file is empty.")
        except Exception as e:
            raise ValueError(f"Corrupted or invalid HDF5 file: {e}")
    elif file_type == 'parquet':
        try:
            import pyarrow.parquet as pq
            pq.ParquetFile(path)
        except Exception as e:
            raise ValueError(f"Corrupted or invalid Parquet file: {e}")
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
    
    return True