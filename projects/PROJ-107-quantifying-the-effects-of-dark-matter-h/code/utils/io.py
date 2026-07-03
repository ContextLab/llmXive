"""
Chunked data I/O utilities for handling large datasets within <7GB RAM constraints.

This module provides generators and utilities to process HDF5/CSV data in chunks,
preventing memory overflow by loading and processing data in manageable segments.
"""
import os
import gc
import h5py
import pandas as pd
import numpy as np
from typing import Generator, List, Dict, Any, Optional, Callable, Union
from pathlib import Path

from utils.config import get_data_raw_path, get_data_processed_path, get_project_root


def iter_hdf5_groups(
    file_path: Union[str, Path],
    group_path: str = "/",
    chunk_size: int = 1000
) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Iterate over groups in an HDF5 file in chunks to avoid loading the entire file into memory.
    
    Args:
        file_path: Path to the HDF5 file.
        group_path: The HDF5 group path to iterate over (e.g., "/").
        chunk_size: Number of groups to process per chunk.
        
    Yields:
        A list of dictionaries, each containing the data for one group (halo) in the chunk.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"HDF5 file not found: {file_path}")
    
    with h5py.File(file_path, 'r') as f:
        # Navigate to the target group
        if group_path not in f:
            raise ValueError(f"Group path '{group_path}' not found in {file_path}")
        
        target_group = f[group_path]
        
        # Get list of group names (halo IDs)
        group_names = [name for name in target_group.keys() if isinstance(target_group[name], h5py.Group)]
        
        for i in range(0, len(group_names), chunk_size):
            chunk = []
            current_names = group_names[i:i + chunk_size]
            
            for name in current_names:
                try:
                    group = target_group[name]
                    data = {}
                    # Extract basic metadata
                    if 'id' in group.attrs:
                        data['halo_id'] = int(group.attrs['id'])
                    else:
                        data['halo_id'] = int(name)
                    
                    # Extract mass (if available)
                    if 'mass' in group.attrs:
                        data['mass'] = float(group.attrs['mass'])
                    
                    # Extract particle count (if available)
                    if 'num_part' in group.attrs:
                        data['num_part'] = int(group.attrs['num_part'])
                    
                    # Try to read position or other arrays if needed
                    # Only read small arrays here to keep memory low
                    for key in group.keys():
                        dataset = group[key]
                        if dataset.shape == ():
                            data[key] = float(dataset[()])
                        elif dataset.shape[0] <= 10: # Small arrays only
                            data[key] = dataset[()]
                    
                    chunk.append(data)
                    
                    # Force garbage collection periodically within the chunk loop
                    if len(chunk) % 50 == 0:
                        gc.collect()
                        
                except Exception as e:
                    # Log error but continue to next halo
                    print(f"Warning: Failed to read group {name} in {file_path}: {e}")
                    continue
            
            if chunk:
                yield chunk
                # Explicitly clear reference to chunk data before yielding next
                chunk = None
                gc.collect()


def iter_csv_chunks(
    file_path: Union[str, Path],
    chunk_size: int = 5000,
    **kwargs
) -> Generator[pd.DataFrame, None, None]:
    """
    Iterate over a CSV file in chunks using pandas.
    
    Args:
        file_path: Path to the CSV file.
        chunk_size: Number of rows per chunk.
        **kwargs: Additional arguments passed to pd.read_csv.
        
    Yields:
        Pandas DataFrame containing a chunk of the CSV data.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    for chunk in pd.read_csv(file_path, chunksize=chunk_size, **kwargs):
        yield chunk
        gc.collect()


def save_dataframe_chunked(
    df: pd.DataFrame,
    output_path: Union[str, Path],
    chunk_size: int = 10000,
    mode: str = 'w'
) -> None:
    """
    Save a large DataFrame to CSV in chunks to avoid memory issues during I/O.
    
    Args:
        df: The DataFrame to save.
        output_path: Path to the output CSV file.
        chunk_size: Number of rows per write chunk.
        mode: Write mode ('w' for write, 'a' for append).
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    total_rows = len(df)
    
    for i in range(0, total_rows, chunk_size):
        chunk = df.iloc[i:i + chunk_size]
        # Write header only on the first chunk if mode is 'w'
        write_header = (mode == 'w' and i == 0)
        chunk.to_csv(
            output_path,
            mode='a',
            header=write_header,
            index=False
        )
        gc.collect()


def load_config_safe(config_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Safely load a YAML configuration file.
    
    Args:
        config_path: Path to the YAML file.
        
    Returns:
        Dictionary containing the configuration.
    """
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def validate_hdf5_structure(file_path: Union[str, Path], required_groups: List[str]) -> bool:
    """
    Validate that an HDF5 file contains the required groups.
    
    Args:
        file_path: Path to the HDF5 file.
        required_groups: List of required group paths.
        
    Returns:
        True if all required groups exist, False otherwise.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return False
    
    with h5py.File(file_path, 'r') as f:
        for group_path in required_groups:
            if group_path not in f:
                return False
    return True


def get_file_size_mb(file_path: Union[str, Path]) -> float:
    """
    Get the size of a file in MB.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        File size in MB.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return 0.0
    return file_path.stat().st_size / (1024 * 1024)


def process_halo_chunk(
    chunk: List[Dict[str, Any]],
    processor_func: Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    """
    Process a chunk of halo data using a provided processor function.
    
    Args:
        chunk: List of halo data dictionaries.
        processor_func: Function that takes a halo dict and returns processed dict or None.
        
    Returns:
        List of processed halo data dictionaries.
    """
    results = []
    for halo_data in chunk:
        try:
            processed = processor_func(halo_data)
            if processed is not None:
                results.append(processed)
        except Exception as e:
            print(f"Warning: Failed to process halo {halo_data.get('halo_id', 'unknown')}: {e}")
            continue
    return results
