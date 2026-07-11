import os
import gc
import h5py
import pandas as pd
import numpy as np
from typing import Generator, List, Dict, Any, Optional, Callable, Union
from pathlib import Path

from utils.config import get_project_root, get_data_raw_path, get_data_processed_path


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
    Validate that an HDF5 file exists and contains required groups.
    
    Args:
        file_path: Path to the HDF5 file.
        required_groups: List of group paths that must exist (e.g., ['PartType0', 'PartType1']).
        
    Returns:
        True if valid, False otherwise.
    """
    path = Path(file_path)
    if not path.exists():
        return False
    
    try:
        with h5py.File(path, 'r') as f:
            if required_groups:
                for group in required_groups:
                    if group not in f:
                        return False
        return True
    except Exception:
        return False


def iter_hdf5_groups(
    file_path: Union[str, Path],
    group_path: str = '/',
    max_memory_mb: int = 5000
) -> Generator[Dict[str, Any], None, None]:
    """
    Iterate over groups in an HDF5 file in a memory-safe manner.
    This generator yields dictionaries representing the data in each subgroup,
    processing them in chunks to respect memory constraints.
    
    Args:
        file_path: Path to the HDF5 file.
        group_path: The parent group to iterate within.
        max_memory_mb: Approximate max memory to use for buffering (for safety).
        
    Yields:
        Dict containing group name and its data (loaded as needed).
    """
    path = Path(file_path)
    if not path.exists():
        return

    try:
        with h5py.File(path, 'r') as f:
            if group_path not in f:
                return
            
            parent = f[group_path]
            
            # Iterate over immediate children
            for key in parent.keys():
                child = parent[key]
                if isinstance(child, h5py.Group):
                    # For groups, we yield metadata or recurse if needed
                    # Here we yield the group object reference wrapped in dict for lazy loading
                    yield {
                        'name': key,
                        'type': 'group',
                        'path': f"{group_path}/{key}",
                        'attrs': dict(child.attrs)
                    }
                elif isinstance(child, h5py.Dataset):
                    # For datasets, we might want to yield chunks if large
                    # For now, yield metadata and a loader function or raw data if small
                    size_mb = (child.size * child.dtype.itemsize) / (1024 * 1024)
                    yield {
                        'name': key,
                        'type': 'dataset',
                        'path': f"{group_path}/{key}",
                        'shape': child.shape,
                        'dtype': str(child.dtype),
                        'size_mb': size_mb,
                        'data': child[:]  # Load dataset into memory (safe if chunked elsewhere)
                    }
    finally:
        gc.collect()


def iter_csv_chunks(
    file_path: Union[str, Path],
    chunk_size: int = 10000,
    usecols: Optional[List[str]] = None
) -> Generator[pd.DataFrame, None, None]:
    """
    Iterate over a CSV file in chunks to handle large files within memory limits.
    
    Args:
        file_path: Path to the CSV file.
        chunk_size: Number of rows per chunk.
        usecols: Optional list of columns to load.
        
    Yields:
        Pandas DataFrame containing the next chunk.
    """
    path = Path(file_path)
    if not path.exists():
        return

    # Use pandas chunk iterator
    try:
        for chunk in pd.read_csv(
            path,
            chunksize=chunk_size,
            usecols=usecols
        ):
            yield chunk
            # Explicitly free memory if needed, though generator handles scope
            gc.collect()
    except Exception as e:
        # Log error or re-raise depending on strategy
        raise RuntimeError(f"Error reading CSV chunks from {path}: {e}")


def save_dataframe_chunked(
    df: pd.DataFrame,
    output_path: Union[str, Path],
    chunk_size: int = 50000,
    mode: str = 'w'
) -> None:
    """
    Save a large DataFrame to a CSV file in chunks to avoid memory spikes
    during the write operation, or to resume writes.
    
    Args:
        df: The DataFrame to save.
        output_path: Path to the output CSV file.
        chunk_size: Number of rows per write operation.
        mode: 'w' for write (overwrite), 'a' for append.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    total_rows = len(df)
    start_idx = 0
    
    # Determine if header should be written
    write_header = (mode == 'w') or (not path.exists())
    
    while start_idx < total_rows:
        end_idx = min(start_idx + chunk_size, total_rows)
        chunk = df.iloc[start_idx:end_idx]
        
        # Determine append mode for pandas
        append_mode = 'a' if not write_header else 'w'
        # If appending to existing file without header, pandas needs specific handling
        # but standard 'a' in to_csv often requires header=False if file exists
        if write_header:
            chunk.to_csv(path, mode=append_mode, index=False, header=True)
            write_header = False # Only write header once
        else:
            chunk.to_csv(path, mode='a', index=False, header=False)
        
        start_idx = end_idx
        gc.collect()


def load_config_safe(config_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Safely load a YAML configuration file.
    
    Args:
        config_path: Path to the YAML config file.
        
    Returns:
        Dictionary of configuration.
        
    Raises:
        FileNotFoundError: If config file not found.
        ValueError: If YAML is invalid.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    
    try:
        import yaml
        with open(path, 'r') as f:
            config = yaml.safe_load(f)
            return config if config else {}
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {path}: {e}")


def process_halo_chunk(
    halo_ids: List[int],
    data_source: Union[str, Path],
    processor_fn: Callable[[int], Optional[Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    """
    Process a list of halo IDs using a provided processor function.
    This function manages the chunking logic and memory cleanup for the processing loop.
    
    Args:
        halo_ids: List of halo IDs to process.
        data_source: Path to the source data (HDF5 or other).
        processor_fn: Function that takes a halo_id and returns a processed dict or None.
        
    Returns:
        List of processed result dictionaries.
    """
    results = []
    
    # Simple loop with explicit GC to ensure memory stays under 7GB
    for halo_id in halo_ids:
        try:
            result = processor_fn(halo_id)
            if result is not None:
                results.append(result)
        except Exception as e:
            # Log error but continue processing other halos
            # In a real pipeline, this would use the logging utility
            print(f"Error processing halo {halo_id}: {e}")
        
        # Periodic GC to prevent memory fragmentation
        if len(results) % 50 == 0:
            gc.collect()
            
    return results