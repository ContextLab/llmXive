import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# Import utilities from existing project modules
from setup_logging import setup_logging, get_data_quality_logger
from config import get_path_env_override

# Ensure we can import from the project root
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# --- Logging Setup ---
def ensure_directories():
    """Ensure required output directories exist."""
    dirs = [
        PROJECT_ROOT / "data" / "raw" / "era5_raw_chunks",
        PROJECT_ROOT / "data" / "raw",
        PROJECT_ROOT / "results" / "logs"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_logger():
    """Get the project logger."""
    return get_data_quality_logger()

def append_log(msg: str, log_path: Path):
    """Append a message to a log file."""
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")

# --- Core Logic ---

def load_fetch_status(status_path: Path) -> List[Dict[str, Any]]:
    """
    Load the list of requested tiles and their status from fetch_status.json.
    Raises FileNotFoundError if the file does not exist.
    """
    if not status_path.exists():
        raise FileNotFoundError(f"Fetch status file not found: {status_path}")
    
    with open(status_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Ensure we return a list of tiles
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "tiles" in data:
        return data["tiles"]
    else:
        # Fallback: treat the whole JSON as a single tile or list
        return [data] if isinstance(data, dict) else data

def stream_tile_to_parquet(tile_info: Dict[str, Any], chunk_dir: Path) -> Optional[Path]:
    """
    Stream a specific tile from the raw chunks directory to a Parquet file.
    
    Args:
        tile_info: Dictionary containing tile metadata (e.g., 'tile_id', 'status', 'path').
        chunk_dir: Directory where raw chunks (NetCDF or intermediate) are stored.
    
    Returns:
        Path to the generated Parquet file, or None if processing failed.
    """
    tile_id = tile_info.get("tile_id")
    status = tile_info.get("status")
    raw_path_str = tile_info.get("path")
    
    if status != "completed":
        logging.warning(f"Skipping tile {tile_id} with status: {status}")
        return None
    
    if not raw_path_str:
        logging.error(f"Tile {tile_id} has no path specified.")
        return None
    
    raw_path = Path(raw_path_str)
    if not raw_path.exists():
        logging.error(f"Raw chunk for tile {tile_id} not found at {raw_path}")
        return None
    
    # Determine output Parquet path
    parquet_filename = f"{tile_id}.parquet"
    parquet_path = chunk_dir / parquet_filename
    
    if parquet_path.exists():
        logging.info(f"Parquet for {tile_id} already exists, skipping.")
        return parquet_path

    try:
        # Attempt to read the raw chunk. 
        # Depending on the format of 'era5_raw_chunks', it might be NetCDF (needs xarray) 
        # or already a CSV/JSON. 
        # Given the task context (ERA5), NetCDF is standard.
        # We assume xarray is available as a dependency for ERA5 handling.
        import xarray as xr
        
        logging.info(f"Reading raw chunk: {raw_path}")
        ds = xr.open_dataset(raw_path)
        
        # Convert to Pandas DataFrame for Parquet compatibility
        # Reset index to make coordinates columns
        df = ds.reset_index().to_pandas()
        
        # Basic validation: ensure non-empty
        if df.empty:
            logging.warning(f"Tile {tile_id} resulted in empty DataFrame.")
            return None
        
        # Write to Parquet
        logging.info(f"Writing Parquet: {parquet_path}")
        df.to_parquet(parquet_path, index=False)
        
        return parquet_path
    
    except ImportError:
        logging.error("xarray is required to read ERA5 NetCDF chunks but is not installed.")
        raise
    except Exception as e:
        logging.error(f"Failed to process tile {tile_id}: {e}")
        return None

def concatenate_parquet_chunks(chunk_dir: Path, output_path: Path) -> bool:
    """
    Concatenate all Parquet chunks in the directory into a single file.
    """
    parquet_files = sorted(chunk_dir.glob("*.parquet"))
    
    if not parquet_files:
        logging.error("No Parquet chunks found to concatenate.")
        return False
    
    logging.info(f"Concatenating {len(parquet_files)} chunks into {output_path}")
    
    try:
        # Read all chunks into a list of DataFrames
        dfs = [pd.read_parquet(f) for f in parquet_files]
        
        if not dfs:
            return False
        
        # Concatenate
        full_df = pd.concat(dfs, ignore_index=True)
        
        # Verify size
        if full_df.empty:
            logging.error("Concatenated DataFrame is empty.")
            return False
        
        # Write final output
        full_df.to_parquet(output_path, index=False)
        logging.info(f"Successfully wrote {output_path} with {len(full_df)} rows.")
        return True
    
    except Exception as e:
        logging.error(f"Failed to concatenate chunks: {e}")
        return False

def re_execute_fetch(fetch_script_path: Path, status_path: Path, max_retries: int = 3):
    """
    Re-execute the fetch script if the full dataset is missing.
    This is a fallback mechanism as per task requirements.
    """
    for attempt in range(1, max_retries + 1):
        logging.warning(f"Attempt {attempt}/{max_retries}: Re-executing fetch script...")
        
        try:
            # Run the fetch script as a subprocess
            # Assuming the script is in code/fetch_era_full.py or similar
            # We use sys.executable to ensure we use the current environment
            import subprocess
            
            # Determine the actual fetch script to run based on project structure
            # The task references T002c which uses fetch_era_full.py
            fetch_script = PROJECT_ROOT / "code" / "fetch_era_full.py"
            
            if not fetch_script.exists():
                logging.error(f"Fetch script not found: {fetch_script}")
                raise FileNotFoundError(f"Fetch script missing: {fetch_script}")
            
            result = subprocess.run(
                [sys.executable, str(fetch_script)],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logging.info("Fetch script completed successfully.")
                return True
            else:
                logging.error(f"Fetch script failed: {result.stderr}")
        
        except Exception as e:
            logging.error(f"Re-execution attempt {attempt} failed: {e}")
        
        if attempt < max_retries:
            time.sleep(5) # Exponential backoff could be added here
    
    raise RuntimeError(f"Failed to fetch data after {max_retries} retries.")

def main():
    """
    Main entry point for T002d: Stream & Save ERA5 Chunks.
    """
    ensure_directories()
    logger = get_logger()
    logger.info("Starting T002d: Stream & Save ERA5 Chunks")
    
    # Define paths
    fetch_status_path = PROJECT_ROOT / "results" / "logs" / "fetch_status.json"
    chunk_dir = PROJECT_ROOT / "data" / "raw" / "era5_raw_chunks"
    output_file = PROJECT_ROOT / "data" / "raw" / "era5_full.parquet"
    
    # Check if output already exists
    if output_file.exists():
        logger.info(f"Output file {output_file} already exists. Verifying size...")
        if output_file.stat().st_size > 0:
            logger.info("Output file is valid. Exiting.")
            return 0
        else:
            logger.warning("Output file exists but is empty. Removing and regenerating.")
            output_file.unlink()
    
    # Load fetch status
    try:
        tiles = load_fetch_status(fetch_status_path)
    except FileNotFoundError:
        logger.error("Fetch status file missing. Attempting to re-execute fetch.")
        re_execute_fetch(PROJECT_ROOT / "code" / "fetch_era_full.py", fetch_status_path)
        # Reload after re-execution
        tiles = load_fetch_status(fetch_status_path)
    
    # Process tiles
    processed_paths = []
    for tile in tiles:
        result_path = stream_tile_to_parquet(tile, chunk_dir)
        if result_path:
            processed_paths.append(result_path)
    
    if not processed_paths:
        logger.error("No tiles were successfully processed.")
        # If no chunks exist, try to re-fetch one last time
        logger.warning("Attempting re-fetch as no chunks were found.")
        re_execute_fetch(PROJECT_ROOT / "code" / "fetch_era_full.py", fetch_status_path)
        tiles = load_fetch_status(fetch_status_path)
        for tile in tiles:
            result_path = stream_tile_to_parquet(tile, chunk_dir)
            if result_path:
                processed_paths.append(result_path)
        
        if not processed_paths:
            raise RuntimeError("Failed to process any tiles after re-fetch attempt.")
    
    # Concatenate
    success = concatenate_parquet_chunks(chunk_dir, output_file)
    
    if success:
        logger.info("T002d completed successfully.")
        return 0
    else:
        logger.error("T002d failed to produce output.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
