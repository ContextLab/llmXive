import os
import gc
import h5py
import pandas as pd
import numpy as np
import json
import logging
import csv
import hashlib
from pathlib import Path
from typing import Iterator, List, Dict, Any, Optional, Union, TextIO, BinaryIO
from contextlib import contextmanager

from utils.config import get_project_root, get_data_processed_path, get_data_raw_path

# Configure logger for this module
logger = logging.getLogger(__name__)

CHUNK_SIZE = 10000  # Number of rows per chunk for streaming operations

def get_file_size_mb(file_path: Union[str, Path]) -> float:
    """
    Get the size of a file in megabytes.

    Args:
        file_path: Path to the file.

    Returns:
        Size in MB.
    """
    path = Path(file_path)
    if not path.exists():
        return 0.0
    return path.stat().st_size / (1024 * 1024)

def validate_hdf5_structure(file_path: Union[str, Path], required_groups: Optional[List[str]] = None) -> bool:
    """
    Validate the structure of an HDF5 file.

    Args:
        file_path: Path to the HDF5 file.
        required_groups: Optional list of group names that must exist.

    Returns:
        True if valid, False otherwise.
    """
    path = Path(file_path)
    if not path.exists():
        logger.error(f"HDF5 file not found: {path}")
        return False

    try:
        with h5py.File(path, 'r') as f:
            if required_groups:
                for group_name in required_groups:
                    if group_name not in f:
                        logger.error(f"Missing required group '{group_name}' in {path}")
                        return False
        return True
    except Exception as e:
        logger.error(f"Error validating HDF5 structure for {path}: {e}")
        return False

def iter_hdf5_groups(file_path: Union[str, Path], group_name: str, chunk_size: int = CHUNK_SIZE) -> Iterator[pd.DataFrame]:
    """
    Iterate over an HDF5 dataset in chunks to avoid loading the entire file into memory.

    Args:
        file_path: Path to the HDF5 file.
        group_name: Name of the group/dataset to read (e.g., '/PartType0/Coordinates').
        chunk_size: Number of rows to read per chunk.

    Yields:
        pandas DataFrames containing chunks of the data.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"HDF5 file not found: {path}")

    try:
        with h5py.File(path, 'r') as f:
            if group_name not in f:
                raise ValueError(f"Group '{group_name}' not found in {path}")

            dataset = f[group_name]
            total_rows = dataset.shape[0]
            logger.info(f"Iterating {total_rows} rows from {group_name} in {path}")

            for start in range(0, total_rows, chunk_size):
                end = min(start + chunk_size, total_rows)
                chunk = dataset[start:end]
                # Convert to DataFrame if necessary, assuming 2D or 1D data
                if len(chunk.shape) == 2:
                    df = pd.DataFrame(chunk)
                else:
                    df = pd.DataFrame({group_name.split('/')[-1]: chunk})
                yield df
                # Explicitly delete chunk to free memory
                del chunk
                gc.collect()
    except Exception as e:
        logger.error(f"Error iterating HDF5 groups in {path}: {e}")
        raise

def iter_csv_chunks(file_path: Union[str, Path], chunk_size: int = CHUNK_SIZE) -> Iterator[pd.DataFrame]:
    """
    Iterate over a CSV file in chunks.

    Args:
        file_path: Path to the CSV file.
        chunk_size: Number of rows to read per chunk.

    Yields:
        pandas DataFrames containing chunks of the data.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    logger.info(f"Iterating CSV chunks from {path}")
    for chunk in pd.read_csv(path, chunksize=chunk_size):
        yield chunk
        gc.collect()

def save_dataframe_chunked(df: pd.DataFrame, output_path: Union[str, Path], chunk_size: int = CHUNK_SIZE, mode: str = 'w') -> None:
    """
    Save a large DataFrame to CSV in chunks to manage memory and I/O.

    Args:
        df: The DataFrame to save.
        output_path: Path to the output CSV file.
        chunk_size: Number of rows per chunk.
        mode: Write mode ('w' for write, 'a' for append).
    """
    path = Path(output_path)
    logger.info(f"Saving DataFrame to {path} in chunks of {chunk_size}")

    # If mode is 'w', we need to write headers for the first chunk
    write_header = (mode == 'w')

    for start in range(0, len(df), chunk_size):
        end = min(start + chunk_size, len(df))
        chunk_df = df.iloc[start:end]
        chunk_df.to_csv(path, mode=mode, header=write_header, index=False, line_terminator='\n')
        write_header = False  # Subsequent chunks do not need headers
        del chunk_df
        gc.collect()

def load_config_safe(config_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a YAML configuration file safely.

    Args:
        config_path: Path to the YAML config file.

    Returns:
        Dictionary containing configuration.
    """
    path = Path(config_path)
    if not path.exists():
        logger.warning(f"Config file not found: {path}, returning empty config")
        return {}

    import yaml
    try:
        with open(path, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"Error loading config {path}: {e}")
        return {}

def write_csv_with_associational_flag(output_path: Union[str, Path], df: pd.DataFrame, flag_value: str = "true") -> None:
    """
    Write a DataFrame to CSV with a metadata comment header indicating associational-only status.

    Args:
        output_path: Path to the output CSV file.
        df: The DataFrame to write.
        flag_value: The value for the associational_only flag.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Writing CSV with associational flag to {path}")

    # Write the comment header
    with open(path, 'w', newline='') as f:
        f.write(f"# associational_only={flag_value}\n")

    # Append the CSV data
    df.to_csv(path, mode='a', index=False, line_terminator='\n')

def write_json_with_associational_flag(output_path: Union[str, Path], data: Union[Dict, List], flag_value: bool = True) -> None:
    """
    Write data to JSON with an associational-only flag included.

    Args:
        output_path: Path to the output JSON file.
        data: The data to write (dict or list).
        flag_value: The value for the associational_only flag.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Writing JSON with associational flag to {path}")

    # Ensure the flag is present
    if isinstance(data, dict):
        data['associational_only'] = flag_value
    elif isinstance(data, list):
        # If it's a list of records, we might need to wrap it or add to each
        # Assuming the top-level structure is a dict or we wrap it
        data = {"records": data, "associational_only": flag_value}
    else:
        data = {"data": data, "associational_only": flag_value}

    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def process_halo_chunk(chunk_df: pd.DataFrame, halo_id_col: str = 'halo_id') -> pd.DataFrame:
    """
    Process a chunk of halo data. This is a placeholder for specific processing logic
    that might be applied to chunks before aggregation.

    Args:
        chunk_df: DataFrame chunk.
        halo_id_col: Name of the halo ID column.

    Returns:
        Processed DataFrame chunk.
    """
    # Example: Ensure halo_id is integer
    if halo_id_col in chunk_df.columns:
        chunk_df[halo_id_col] = chunk_df[halo_id_col].astype(int)
    return chunk_df

@contextmanager
def managed_hdf5_reader(file_path: Union[str, Path], mode: str = 'r'):
    """
    Context manager for handling HDF5 file operations safely.

    Args:
        file_path: Path to the HDF5 file.
        mode: File mode (r, r+, w, etc.).

    Yields:
        h5py.File object.
    """
    path = Path(file_path)
    f = None
    try:
        f = h5py.File(path, mode)
        yield f
    finally:
        if f is not None:
            f.close()
            gc.collect()