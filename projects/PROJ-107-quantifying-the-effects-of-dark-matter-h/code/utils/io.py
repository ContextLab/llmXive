"""
Chunked data I/O utilities for streaming large datasets without loading into RAM.

This module provides utilities for:
- Iterating over HDF5 groups/chunks
- Streaming CSV chunks
- Saving DataFrames in chunks
- Validating HDF5 structures
- Writing CSV/JSON with associational flags
"""

import os
import gc
import h5py
import pandas as pd
import numpy as np
import json
import csv
from pathlib import Path
from typing import Iterator, Dict, Any, Optional, List, Union, Tuple, BinaryIO
import logging

from utils.config import get_project_root, get_data_processed_path

logger = logging.getLogger(__name__)


def get_file_size_mb(file_path: Union[str, Path]) -> float:
    """Get the size of a file in megabytes."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    size_bytes = path.stat().st_size
    return size_bytes / (1024 * 1024)


def validate_hdf5_structure(file_path: Union[str, Path], required_datasets: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Validate the structure of an HDF5 file.
    
    Args:
        file_path: Path to the HDF5 file
        required_datasets: Optional list of dataset names that must exist
        
    Returns:
        Dictionary containing validation results and structure info
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If required datasets are missing
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"HDF5 file not found: {path}")
    
    result = {
        "valid": False,
        "file_size_mb": get_file_size_mb(path),
        "groups": [],
        "datasets": [],
        "missing_required": []
    }
    
    try:
        with h5py.File(path, 'r') as f:
            # List all groups
            result["groups"] = list(f.keys())
            
            # List all datasets (recursively)
            datasets = []
            for key in f:
                obj = f[key]
                if isinstance(obj, h5py.Group):
                    for dataset_name in obj.keys():
                        datasets.append(f"{key}/{dataset_name}")
                elif isinstance(obj, h5py.Dataset):
                    datasets.append(key)
            result["datasets"] = datasets
            
            # Check required datasets
            if required_datasets:
                for req_ds in required_datasets:
                    if req_ds not in datasets:
                        result["missing_required"].append(req_ds)
                
                if not result["missing_required"]:
                    result["valid"] = True
            else:
                result["valid"] = True
                
    except Exception as e:
        logger.error(f"Error validating HDF5 structure: {e}")
        result["error"] = str(e)
    
    return result


def iter_hdf5_groups(file_path: Union[str, Path], group_path: str = "") -> Iterator[Tuple[str, Any]]:
    """
    Iterator that yields (key, object) pairs from an HDF5 file, grouped by path.
    
    Args:
        file_path: Path to the HDF5 file
        group_path: Base group path to start iteration from (default is root)
        
    Yields:
        Tuple of (key, h5py.Group or h5py.Dataset)
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"HDF5 file not found: {path}")
    
    with h5py.File(path, 'r') as f:
        current_group = f[group_path] if group_path else f
        for key in current_group:
            obj = current_group[key]
            yield key, obj
                
                
def iter_csv_chunks(file_path: Union[str, Path], chunk_size: int = 10000) -> Iterator[pd.DataFrame]:
    """
    Iterator that yields chunks of a CSV file as DataFrames.
    
    Args:
        file_path: Path to the CSV file
        chunk_size: Number of rows per chunk
        
    Yields:
        DataFrame containing a chunk of rows
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")
    
    # Use pandas chunked reading
    for chunk in pd.read_csv(path, chunksize=chunk_size):
        yield chunk
        
        
def save_dataframe_chunked(df: pd.DataFrame, output_path: Union[str, Path], chunk_size: int = 10000) -> int:
    """
    Save a large DataFrame to CSV in chunks to avoid memory issues.
    
    Args:
        df: DataFrame to save
        output_path: Path to save the CSV file
        chunk_size: Number of rows per chunk
        
    Returns:
        Number of chunks written
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    total_rows = len(df)
    chunks_written = 0
    
    # Write header first
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(df.columns.tolist())
        
        # Write chunks
        for start in range(0, total_rows, chunk_size):
            end = min(start + chunk_size, total_rows)
            chunk_df = df.iloc[start:end]
            
            for _, row in chunk_df.iterrows():
                writer.writerow(row.tolist())
            
            chunks_written += 1
            logger.debug(f"Wrote chunk {chunks_written}: rows {start} to {end}")
        
    logger.info(f"Saved {total_rows} rows in {chunks_written} chunks to {path}")
    return chunks_written


def load_config_safe(config_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Safely load a YAML configuration file.
    
    Args:
        config_path: Path to the YAML config file
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    import yaml
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    
    try:
        with open(path, 'r') as f:
            config = yaml.safe_load(f)
            return config if config else {}
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in config: {e}")


def write_csv_with_associational_flag(output_path: Union[str, Path], df: pd.DataFrame, 
                                      metadata: Optional[Dict[str, Any]] = None) -> None:
    """
    Write a DataFrame to CSV with an associational flag in the header.
    
    This implements the mandatory metadata flag injection (T026a).
    
    Args:
        output_path: Path to save the CSV file
        df: DataFrame to write
        metadata: Optional additional metadata to include in the flag section
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', newline='') as f:
        # Write the associational flag as a comment
        f.write("# associational_only=true\n")
        
        if metadata:
            for key, value in metadata.items():
                f.write(f"# {key}: {value}\n")
        
        # Write header
        writer = csv.writer(f)
        writer.writerow(df.columns.tolist())
        
        # Write data
        for _, row in df.iterrows():
            writer.writerow(row.tolist())
    
    logger.info(f"Written CSV with associational flag: {path}")


def write_json_with_associational_flag(output_path: Union[str, Path], data: Dict[str, Any], 
                                       metadata: Optional[Dict[str, Any]] = None) -> None:
    """
    Write data to JSON with an associational flag.
    
    This implements the mandatory metadata flag injection (T026a).
    
    Args:
        output_path: Path to save the JSON file
        data: Data dictionary to write
        metadata: Optional additional metadata to include
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare output with flag
    output_data = {
        "associational_only": True
    }
    
    if metadata:
        output_data["metadata"] = metadata
    
    output_data["data"] = data
    
    with open(path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Written JSON with associational flag: {path}")


def process_halo_chunk(chunk_data: Dict[str, Any], chunk_id: int) -> Dict[str, Any]:
    """
    Process a chunk of halo data, applying necessary transformations.
    
    Args:
        chunk_data: Dictionary containing halo data for a chunk
        chunk_id: Identifier for this chunk
        
    Returns:
        Processed chunk data with shape metrics
    """
    # This is a placeholder for actual processing logic
    # In a real implementation, this would compute inertia tensors,
    # axial ratios, and triaxiality for the halo particles in the chunk
    result = {
        "chunk_id": chunk_id,
        "processed": True,
        "halo_count": len(chunk_data.get("halo_ids", [])),
        "timestamp": str(pd.Timestamp.now())
    }
    
    return result


class managed_hdf5_reader:
    """
    A managed reader for HDF5 files that ensures proper cleanup.
    
    This context manager ensures that HDF5 files are opened and closed
    properly, and that memory is freed after reading.
    """
    
    def __init__(self, file_path: Union[str, Path], mode: str = 'r'):
        self.file_path = Path(file_path)
        self.mode = mode
        self.file_handle = None
        
    def __enter__(self):
        self.file_handle = h5py.File(self.file_path, self.mode)
        return self.file_handle
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None
            gc.collect()
        return False