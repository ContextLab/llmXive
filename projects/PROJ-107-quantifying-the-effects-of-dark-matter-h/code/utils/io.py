import os
import gc
import h5py
import pandas as pd
import numpy as np
import json
from typing import Generator, List, Dict, Any, Optional, Callable, Union
from pathlib import Path
import logging

from utils.config import get_project_root, get_data_processed_path, get_output_path

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Utility: Associational Flag Injection
# --------------------------------------------------------------------------
# This module now enforces the T026 requirement: all CSV and JSON writers
# must include the "associational_only" flag to explicitly mark that
# the data represents correlational/observational findings, not causal
# claims.

CSV_ASSOCIATIONAL_HEADER = "# associational_only=true"
JSON_ASSOCIATIONAL_KEY = "associational_only"
JSON_ASSOCIATIONAL_VALUE = True

def write_csv_with_associational_flag(
    filepath: Union[str, Path],
    df: pd.DataFrame,
    mode: str = 'w'
) -> None:
    """
    Writes a pandas DataFrame to a CSV file, prepending the mandatory
    associational flag as a comment header.

    Args:
        filepath: Path to the output CSV.
        df: DataFrame to write.
        mode: File write mode ('w' for overwrite, 'a' for append).
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Write the header comment first
    with open(filepath, mode) as f:
        f.write(f"{CSV_ASSOCIATIONAL_HEADER}\n")

    # Append the DataFrame content
    df.to_csv(filepath, mode='a', header=False, index=False)
    logger.info(f"Wrote {len(df)} rows to {filepath} with associational flag.")

def write_json_with_associational_flag(
    filepath: Union[str, Path],
    data: Dict[str, Any],
    indent: int = 2
) -> None:
    """
    Writes a dictionary to a JSON file, ensuring the mandatory
    associational flag is included in the root object.

    Args:
        filepath: Path to the output JSON.
        data: Dictionary to write. The 'associational_only' key will be
              added or overwritten.
        indent: JSON indentation level.
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Ensure the flag is present
    data[JSON_ASSOCIATIONAL_KEY] = JSON_ASSOCIATIONAL_VALUE

    with open(filepath, 'w') as f:
        json.dump(data, f, indent=indent)
    logger.info(f"Wrote JSON to {filepath} with associational flag.")

# --------------------------------------------------------------------------
# Existing IO Utilities (Extended)
# --------------------------------------------------------------------------

def get_file_size_mb(filepath: Union[str, Path]) -> float:
    """Get file size in megabytes."""
    filepath = Path(filepath)
    if not filepath.exists():
        return 0.0
    return filepath.stat().st_size / (1024 * 1024)

def validate_hdf5_structure(filepath: Union[str, Path], required_groups: List[str]) -> bool:
    """
    Validates that an HDF5 file contains the required groups.
    """
    filepath = Path(filepath)
    if not filepath.exists():
        logger.error(f"HDF5 file not found: {filepath}")
        return False

    try:
        with h5py.File(filepath, 'r') as f:
            for group in required_groups:
                if group not in f:
                    logger.error(f"Missing group '{group}' in {filepath}")
                    return False
        return True
    except Exception as e:
        logger.error(f"Error validating HDF5 structure for {filepath}: {e}")
        return False

def iter_hdf5_groups(filepath: Union[str, Path], group_name: str) -> Generator[str, None, None]:
    """
    Iterates over subgroups within a specific HDF5 group.
    Yields the names of the subgroups.
    """
    filepath = Path(filepath)
    try:
        with h5py.File(filepath, 'r') as f:
            if group_name in f:
                parent = f[group_name]
                for key in parent.keys():
                    yield key
    except Exception as e:
        logger.error(f"Error iterating HDF5 groups in {filepath}: {e}")
        raise

def iter_csv_chunks(filepath: Union[str, Path], chunksize: int = 100000) -> Generator[pd.DataFrame, None, None]:
    """
    Iterates over a CSV file in chunks, skipping the associational header if present.
    """
    filepath = Path(filepath)
    if not filepath.exists():
        logger.warning(f"CSV file not found for chunking: {filepath}")
        return

    # Check if the file starts with our header
    first_line = ""
    try:
        with open(filepath, 'r') as f:
            first_line = f.readline().strip()
    except Exception:
        pass

    has_header = first_line.startswith(CSV_ASSOCIATIONAL_HEADER)

    try:
        # If it has our header, we need to skip it. pandas read_csv skiprows works with int or list.
        # If skiprows=1, it skips the first line.
        skip = 1 if has_header else 0

        for chunk in pd.read_csv(filepath, chunksize=chunksize, skiprows=skip):
            yield chunk
    except Exception as e:
        logger.error(f"Error reading CSV chunks from {filepath}: {e}")
        raise

def save_dataframe_chunked(
    df: pd.DataFrame,
    filepath: Union[str, Path],
    chunksize: int = 100000
) -> None:
    """
    Saves a large DataFrame to CSV in chunks to manage memory.
    Includes the associational flag header.
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Write header once
    with open(filepath, 'w') as f:
        f.write(f"{CSV_ASSOCIATIONAL_HEADER}\n")

    # Write chunks
    for i in range(0, len(df), chunksize):
        chunk = df.iloc[i:i+chunksize]
        chunk.to_csv(filepath, mode='a', header=False, index=False)

    logger.info(f"Saved {len(df)} rows to {filepath} in chunks.")

def load_config_safe(config_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Safely loads a YAML configuration file.
    """
    config_path = Path(config_path)
    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}, returning empty dict.")
        return {}

    try:
        import yaml
        with open(config_path, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"Failed to load config {config_path}: {e}")
        raise

def process_halo_chunk(
    halo_data: pd.DataFrame,
    processing_fn: Callable[[pd.DataFrame], pd.DataFrame]
) -> pd.DataFrame:
    """
    Applies a processing function to a chunk of halo data.
    Includes error handling and logging.
    """
    try:
        logger.debug(f"Processing halo chunk with {len(halo_data)} rows.")
        result = processing_fn(halo_data)
        logger.debug(f"Processing complete. Output shape: {result.shape}")
        return result
    except Exception as e:
        logger.error(f"Error processing halo chunk: {e}")
        raise