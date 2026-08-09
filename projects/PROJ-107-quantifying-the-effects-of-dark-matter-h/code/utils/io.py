import os
import gc
import h5py
import pandas as pd
import numpy as np
from typing import Generator, List, Dict, Any, Optional, Callable, Union
from pathlib import Path
import logging

# Import config utilities to resolve paths safely
from utils.config import get_project_root, get_data_raw_path, get_data_processed_path

logger = logging.getLogger(__name__)

def get_file_size_mb(file_path: Union[str, Path]) -> float:
    """Get file size in Megabytes."""
    path = Path(file_path)
    if not path.exists():
        return 0.0
    return path.stat().st_size / (1024 * 1024)

def validate_hdf5_structure(file_path: Union[str, Path], required_keys: Optional[List[str]] = None) -> bool:
    """
    Validate that an HDF5 file exists and contains expected keys.
    Returns True if valid, False otherwise.
    """
    path = Path(file_path)
    if not path.exists():
        logger.error(f"HDF5 file not found: {path}")
        return False

    try:
        with h5py.File(path, 'r') as f:
            if required_keys:
                for key in required_keys:
                    if key not in f:
                        logger.error(f"Missing required key '{key}' in {path}")
                        return False
            # Basic sanity check: file is readable
            _ = f.attrs.keys()
        return True
    except Exception as e:
        logger.error(f"Error validating HDF5 structure for {path}: {e}")
        return False

def iter_hdf5_groups(file_path: Union[str, Path], group_name: str = "halos", 
                     chunk_size: int = 1000) -> Generator[Dict[str, Any], None, None]:
    """
    Iterate over a specific group in an HDF5 file in chunks to handle <7GB RAM constraints.
    
    Args:
        file_path: Path to the HDF5 file.
        group_name: Name of the group containing halo data (e.g., "halos").
        chunk_size: Number of halo entries to load per chunk.
        
    Yields:
        A dictionary containing chunked data arrays from the specified group.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"HDF5 file not found: {path}")

    try:
        with h5py.File(path, 'r') as f:
            if group_name not in f:
                raise KeyError(f"Group '{group_name}' not found in {path}")
            
            group = f[group_name]
            # Assume the first dataset in the group represents the halo count
            # In TNG, datasets are usually aligned by index
            if not group:
                return
                
            first_ds_name = list(group.keys())[0]
            total_count = group[first_ds_name].shape[0]
            
            logger.info(f"Processing {group_name} from {path}: {total_count} entries")

            # Determine which keys are arrays (skip metadata strings if any)
            data_keys = []
            for key in group.keys():
                if isinstance(group[key], h5py.Dataset):
                    data_keys.append(key)

            if not data_keys:
                logger.warning(f"No datasets found in group '{group_name}'")
                return

            # Iterate in chunks
            for start_idx in range(0, total_count, chunk_size):
                end_idx = min(start_idx + chunk_size, total_count)
                chunk_data = {}
                
                for key in data_keys:
                    # Read slice
                    chunk_data[key] = group[key][start_idx:end_idx]
                
                # Add index info for reference
                chunk_data['_start_idx'] = start_idx
                chunk_data['_end_idx'] = end_idx
                
                yield chunk_data
                
                # Force garbage collection periodically to maintain memory safety
                if (end_idx // chunk_size) % 10 == 0:
                    gc.collect()

    except Exception as e:
        logger.error(f"Error iterating HDF5 groups in {path}: {e}")
        raise

def iter_csv_chunks(file_path: Union[str, Path], chunk_size: int = 10000) -> Generator[pd.DataFrame, None, None]:
    """
    Iterate over a CSV file in chunks to handle large files in limited memory.
    
    Args:
        file_path: Path to the CSV file.
        chunk_size: Number of rows per chunk.
        
    Yields:
        Pandas DataFrame containing a chunk of rows.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    try:
        for chunk in pd.read_csv(path, chunksize=chunk_size):
            yield chunk
            gc.collect()
    except Exception as e:
        logger.error(f"Error iterating CSV chunks in {path}: {e}")
        raise

def save_dataframe_chunked(df: pd.DataFrame, output_path: Union[str, Path], 
                            chunk_size: int = 50000, mode: str = 'w') -> None:
    """
    Save a large DataFrame to CSV in chunks to avoid memory spikes during write.
    
    Args:
        df: The DataFrame to save.
        output_path: Path to the output CSV file.
        chunk_size: Number of rows per write chunk.
        mode: 'w' for write (overwrite), 'a' for append.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    total_rows = len(df)
    logger.info(f"Saving {total_rows} rows to {path} in chunks of {chunk_size}")

    # Reset index to ensure clean slicing
    df = df.reset_index(drop=True)

    for i in range(0, total_rows, chunk_size):
        end_idx = min(i + chunk_size, total_rows)
        chunk_df = df.iloc[i:end_idx]
        
        # Determine if header is needed
        write_header = (i == 0) and (mode == 'w')
        append_mode = (mode == 'a') or (i > 0)
        
        # If appending, we need to write header if it's the first append chunk
        if append_mode and i == 0:
            write_header = True
        
        chunk_df.to_csv(
            path, 
            mode='a' if (i > 0 or mode == 'a') else 'w', 
            header=write_header, 
            index=False
        )
        
        # Log progress
        if (end_idx // chunk_size) % 5 == 0:
            logger.debug(f"Saved up to row {end_idx}")

    logger.info(f"Finished saving {total_rows} rows to {path}")

def load_config_safe(config_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Safely load a YAML configuration file.
    
    Args:
        config_path: Path to the YAML config file.
        
    Returns:
        Dictionary of configuration values.
        
    Raises:
        FileNotFoundError: If config file does not exist.
        ValueError: If config is invalid.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    
    try:
        import yaml
        with open(path, 'r') as f:
            config = yaml.safe_load(f)
            if config is None:
                config = {}
            return config
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in config {path}: {e}")

def process_halo_chunk(chunk_data: Dict[str, Any], 
                       processor_func: Callable[[Dict[str, Any]], Optional[Dict[str, Any]]],
                       batch_id: int = 0) -> List[Dict[str, Any]]:
    """
    Process a chunk of halo data using a provided processor function.
    This function handles memory management and error logging for chunk processing.
    
    Args:
        chunk_data: Dictionary containing chunked data arrays (e.g., from iter_hdf5_groups).
        processor_func: A function that takes a single halo record (dict) and returns processed data.
                        Returns None if the halo should be skipped.
        batch_id: Identifier for the current batch/chunk for logging.
        
    Returns:
        List of processed halo records.
    """
    if not chunk_data:
        return []

    # Determine number of haloes in this chunk
    # We look for the longest array in the chunk to determine count
    counts = [len(v) for v in chunk_data.values() if isinstance(v, (list, np.ndarray))]
    if not counts:
        return []
    
    num_haloes = max(counts)
    processed_results = []

    # Convert numpy arrays to lists for easier iteration if needed, 
    # but direct indexing is faster for numpy
    for i in range(num_haloes):
        try:
            halo_record = {}
            for key, value in chunk_data.items():
                if key.startswith('_'):
                    continue
                if isinstance(value, np.ndarray):
                    halo_record[key] = value[i]
                elif isinstance(value, list):
                    halo_record[key] = value[i]
                else:
                    halo_record[key] = value
            
            # Apply processor
            result = processor_func(halo_record)
            if result is not None:
                processed_results.append(result)
                
        except Exception as e:
            logger.warning(f"Error processing halo {i} in batch {batch_id}: {e}")
            continue

    logger.debug(f"Processed batch {batch_id}: {num_haloes} input, {len(processed_results)} output")
    return processed_results