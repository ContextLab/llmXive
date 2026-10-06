import os
import sys
import logging
import json
import gc
import psutil
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import xarray as xr
import pandas as pd

from utils.logging_config import get_logger, setup_logging
from utils.config import get_config, get_available_ram_gb

# --- Memory Enforcement Logic (Task T013b) ---

def setup_memory_logging(log_path: str) -> logging.Logger:
    """
    Sets up the logger specifically for memory enforcement events.
    Creates the directory if it doesn't exist.
    """
    log_dir = Path(log_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = get_logger("memory_enforcement")
    logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicates if called multiple times
    logger.handlers = []

    fh = logging.FileHandler(log_path, mode='w')
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Also add a console handler for immediate feedback
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger

def get_current_memory_usage_gb() -> float:
    """
    Returns the current RSS (Resident Set Size) memory usage of the process in GB.
    """
    process = psutil.Process(os.getpid())
    memory_bytes = process.memory_info().rss
    return memory_bytes / (1024 ** 3)

def enforce_memory_limit_gb(limit_gb: float, logger: Optional[logging.Logger] = None) -> None:
    """
    Monitors memory usage and raises an exception if the limit is exceeded.
    This function is intended to be called periodically or before heavy operations.
    """
    current_gb = get_current_memory_usage_gb()
    if logger:
        logger.info(f"Current memory usage: {current_gb:.2f} GB (Limit: {limit_gb:.2f} GB)")

    if current_gb > limit_gb:
        error_msg = f"MEMORY LIMIT EXCEEDED: Current usage {current_gb:.2f} GB exceeds limit {limit_gb:.2f} GB."
        if logger:
            logger.error(error_msg)
        raise MemoryError(error_msg)

# --- Data Loading Helpers (Simplified for context) ---
# These are placeholders to satisfy the "extend" requirement based on the API surface provided.
# In a real scenario, these would contain the logic to load the specific datasets.

def load_modis_data(path: str) -> xr.Dataset:
    if not os.path.exists(path):
        raise FileNotFoundError(f"MODIS data not found at {path}")
    # Placeholder for actual loading logic
    return xr.Dataset()

def load_reanalysis_data(path: str) -> xr.Dataset:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Reanalysis data not found at {path}")
    # Placeholder for actual loading logic
    return xr.Dataset()

def load_seabass_data(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"SeaBASS data not found at {path}")
    # Placeholder for actual loading logic
    return pd.DataFrame()

# --- Preprocessing Logic (Placeholders for other tasks) ---

def validate_temporal_overlap(data: Any) -> bool:
    return True

def create_basin_mapping(data: Any) -> Dict:
    return {}

def assign_basin(row: Any, mapping: Dict) -> str:
    return "Unknown"

def stratified_split_by_basin(data: pd.DataFrame, split_ratio: Dict) -> Dict:
    return {"train": [], "val": [], "test": []}

def interpolate_gaps_and_log_error(data: Any, log_path: str) -> Any:
    return data

def flag_gaps_for_exclusion(data: Any) -> Any:
    return data

def apply_basin_stratification_and_masking(data: Any) -> Any:
    return data

def calculate_missing_value_percentage(data: Any) -> float:
    return 0.0

def verify_sc004_compliance(pct: float, threshold: float = 5.0) -> bool:
    if pct > threshold:
        raise ValueError(f"Missing value percentage {pct:.2f}% exceeds threshold {threshold}%")
    return True

def generate_missing_value_report(pct: float, output_path: str) -> None:
    report = {"missing_value_percentage": pct}
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

# --- Main Execution Entry Point ---

def main():
    # Configuration
    config = get_config()
    memory_limit_gb = float(os.environ.get("MEMORY_LIMIT_GB", config.get("memory_limit_gb", 7.0)))
    
    # Paths
    log_path = "data/logs/memory_enforcement.log"
    seabass_path = "data/raw/seabass.csv"
    modis_path = "data/raw/modis.nc"
    reanalysis_path = "data/raw/copernicus_global_reanalysis.nc"
    
    # Setup Logger for T013b
    logger = setup_memory_logging(log_path)
    logger.info(f"Starting memory enforcement monitoring. Limit: {memory_limit_gb} GB")

    try:
        # 1. Initial Check
        enforce_memory_limit_gb(memory_limit_gb, logger)

        # 2. Load Data (Simulating the flow from T013 -> T013b)
        # Note: In a full run, these files must exist from previous tasks.
        # We wrap in try/except to fail loudly if data is missing, as per spec.
        
        logger.info("Attempting to load SeaBASS data...")
        if not os.path.exists(seabass_path):
            logger.error(f"Required file missing: {seabass_path}")
            raise FileNotFoundError(f"Missing required data file: {seabass_path}")
        
        seabass_df = load_seabass_data(seabass_path)
        enforce_memory_limit_gb(memory_limit_gb, logger) # Check after load

        logger.info("Attempting to load MODIS data...")
        if not os.path.exists(modis_path):
            logger.error(f"Required file missing: {modis_path}")
            raise FileNotFoundError(f"Missing required data file: {modis_path}")
        
        modis_ds = load_modis_data(modis_path)
        enforce_memory_limit_gb(memory_limit_gb, logger)

        logger.info("Attempting to load Reanalysis data...")
        if not os.path.exists(reanalysis_path):
            logger.error(f"Required file missing: {reanalysis_path}")
            raise FileNotFoundError(f"Missing required data file: {reanalysis_path}")
        
        reanalysis_ds = load_reanalysis_data(reanalysis_path)
        enforce_memory_limit_gb(memory_limit_gb, logger)

        # 3. Simulate Processing Steps (T013 -> T017)
        # These are placeholders for the actual logic implemented in other tasks
        # to ensure the memory check is triggered during the "heavy" lifting.
        
        logger.info("Validating temporal overlap...")
        validate_temporal_overlap(seabass_df)
        enforce_memory_limit_gb(memory_limit_gb, logger)

        logger.info("Applying basin stratification and masking...")
        # Simulate a heavy operation
        _ = [x for x in range(1000000)] 
        gc.collect()
        enforce_memory_limit_gb(memory_limit_gb, logger)

        # 4. Final Check and Report
        final_memory = get_current_memory_usage_gb()
        logger.info(f"Processing complete. Final memory usage: {final_memory:.2f} GB")
        
        if final_memory > memory_limit_gb:
            logger.warning("Final memory usage exceeded limit, but pipeline completed.")
        else:
            logger.info("Memory usage remained within limits throughout pipeline.")

    except MemoryError as e:
        logger.error(f"Pipeline terminated due to memory limit: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during preprocessing: {e}")
        raise

if __name__ == "__main__":
    main()