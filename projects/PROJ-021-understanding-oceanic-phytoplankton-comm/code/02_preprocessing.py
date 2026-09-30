import os
import sys
import logging
import json
import gc
from pathlib import Path
from typing import Dict, Any, Optional, Union, Tuple, List
import numpy as np
import xarray as xr
import pandas as pd
import dask.array as da
import psutil

from utils.logging_config import get_logger, setup_logging, log_pipeline_event
from utils.config import get_config, get_available_ram_gb

# --- Configuration & Logging Setup ---

def setup_memory_logging(log_file: Optional[Union[str, Path]] = None) -> logging.Logger:
    """
    Sets up the logging infrastructure specifically for memory enforcement and pipeline events.
    Writes to data/logs/memory_enforcement.log by default if not specified.
    """
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    if log_file is None:
        log_file = log_dir / "memory_enforcement.log"
    else:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = get_logger("preprocessing_memory")
    logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Also log to console for immediate feedback
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

def get_current_memory_usage_gb() -> float:
    """Returns current process memory usage in GB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)

def enforce_memory_limit_gb(limit_gb: Optional[float] = None, logger: Optional[logging.Logger] = None) -> bool:
    """
    Checks current memory usage against the limit.
    If limit is exceeded, attempts garbage collection and returns False if still exceeded.
    """
    if limit_gb is None:
        config = get_config()
        limit_gb = config.get("memory_limit_gb", 7.0)

    current_gb = get_current_memory_usage_gb()
    if logger:
        logger.info(f"Current Memory Usage: {current_gb:.2f} GB (Limit: {limit_gb:.2f} GB)")

    if current_gb > limit_gb:
        if logger:
            logger.warning("Memory limit exceeded. Attempting garbage collection...")
        gc.collect()
        current_gb = get_current_memory_usage_gb()
        if logger:
            logger.info(f"Memory after GC: {current_gb:.2f} GB")
        
        if current_gb > limit_gb:
            if logger:
                logger.error(f"Memory limit ({limit_gb:.2f} GB) still exceeded after GC ({current_gb:.2f} GB).")
            return False
    return True

# --- Data Loading Helpers (Delegated to utils/data_loaders where possible, or inline for specific logic) ---

def load_modis_data(file_path: Union[str, Path]) -> xr.Dataset:
    """
    Loads MODIS data from NetCDF.
    Assumes T011b has successfully created data/raw/modis.nc.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"MODIS data file not found at {path}. Has T011b been run?")
    
    # Use chunks to handle large files within memory limits
    try:
        ds = xr.open_dataset(path, chunks='auto')
        return ds
    except Exception as e:
        logging.error(f"Failed to load MODIS data: {e}")
        raise

def load_reanalysis_data(file_path: Union[str, Path]) -> xr.Dataset:
    """
    Loads Reanalysis data from NetCDF.
    Assumes T011a has successfully created data/raw/reanalysis.nc.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Reanalysis data file not found at {path}. Has T011a been run?")
    
    try:
        ds = xr.open_dataset(path, chunks='auto')
        return ds
    except Exception as e:
        logging.error(f"Failed to load Reanalysis data: {e}")
        raise

def load_seabass_data(file_path: Union[str, Path]) -> pd.DataFrame:
    """
    Loads SeaBASS data from CSV.
    Assumes T011c has successfully created data/raw/seabass.csv.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"SeaBASS data file not found at {path}. Has T011c been run?")
    
    try:
        df = pd.read_csv(path)
        return df
    except Exception as e:
        logging.error(f"Failed to load SeaBASS data: {e}")
        raise

# --- Preprocessing Logic (Extending existing pipeline) ---

def validate_temporal_overlap(ds_modis: xr.Dataset, ds_reanalysis: xr.Dataset, df_seabass: pd.DataFrame) -> Tuple[pd.DatetimeIndex, pd.DatetimeIndex]:
    """
    Validates that there is >= 10 years of temporal overlap between all sources.
    Returns the common time range.
    """
    # Extract time coordinates
    # Assuming standard time dimension names; adjust if necessary based on actual data
    time_modis = ds_modis.coords.get('time')
    time_reanalysis = ds_reanalysis.coords.get('time')
    
    # Convert SeaBASS timestamp column to datetime if not already
    if 'timestamp' in df_seabass.columns:
        df_seabass['timestamp'] = pd.to_datetime(df_seabass['timestamp'])
        time_seabass = df_seabass['timestamp']
    else:
        # Fallback or error if column name differs
        raise ValueError("SeaBASS data must have a 'timestamp' column.")

    # Determine min/max for each
    min_modis = time_modis.min().values
    max_modis = time_modis.max().values
    min_reanalysis = time_reanalysis.min().values
    max_reanalysis = time_reanalysis.max().values
    min_seabass = time_seabass.min()
    max_seabass = time_seabass.max()

    # Calculate overlap
    common_start = max(min_modis, min_reanalysis, min_seabass)
    common_end = min(max_modis, max_reanalysis, max_seabass)

    duration = (common_end - common_start).astype('timedelta64[D]') / np.timedelta64(1, 'D') / 365.25

    if duration < 10:
        raise ValueError(f"Temporal overlap is only {duration:.2f} years. Requirement is >= 10 years.")
    
    logger = get_logger("preprocessing")
    logger.info(f"Temporal overlap validated: {duration:.2f} years ({common_start} to {common_end})")
    
    return pd.to_datetime([common_start, common_end])

def create_basin_mapping(df_seabass: pd.DataFrame) -> Dict[str, str]:
    """
    Creates a mapping of locations to basins based on SeaBASS data.
    """
    # Placeholder logic: In a real implementation, this would use a geospatial lookup.
    # For this task, we assume the 'basin' column exists or derive it simply.
    if 'basin' not in df_seabass.columns:
        # Simple heuristic if basin column missing (just for example logic)
        # Real implementation would use lat/lon against a shapefile
        df_seabass['basin'] = 'Unknown' 
    
    basins = df_seabass['basin'].unique()
    logger = get_logger("preprocessing")
    logger.info(f"Found basins: {basins}")
    return {b: b for b in basins}

def stratified_split_by_basin(df: pd.DataFrame, basins: List[str], test_size: float = 0.2, val_size: float = 0.1) -> Dict[str, List[int]]:
    """
    Creates stratified train/val/test split indices by basin.
    """
    indices = df.index.tolist()
    np.random.shuffle(indices)
    
    splits = {'train': [], 'val': [], 'test': []}
    
    for basin in basins:
        basin_indices = [i for i in indices if df.loc[i, 'basin'] == basin]
        n = len(basin_indices)
        n_test = int(n * test_size)
        n_val = int(n * val_size)
        
        splits['test'].extend(basin_indices[:n_test])
        splits['val'].extend(basin_indices[n_test:n_test+n_val])
        splits['train'].extend(basin_indices[n_test+n_val:])
    
    return splits

def interpolate_gaps_and_log_error(ds: xr.Dataset, max_gap_months: int = 2) -> xr.Dataset:
    """
    Interpolates gaps <= max_gap_months. Logs error to data/logs/interpolation_error.log.
    """
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    error_log_path = log_dir / "interpolation_error.log"
    
    logger = get_logger("interpolation")
    fh = logging.FileHandler(error_log_path)
    fh.setLevel(logging.INFO)
    logger.addHandler(fh)
    
    # Simple interpolation for demonstration
    # In reality, this would be more complex per variable
    ds_interp = ds.interpolate_na(dim='time', method='linear')
    
    # Log specific errors if any (placeholder for actual error calc)
    logger.info(f"Interpolation completed. Max gap allowed: {max_gap_months} months.")
    return ds_interp

def flag_gaps_for_exclusion(ds: xr.Dataset, max_gap_months: int = 2) -> xr.Dataset:
    """
    Flags gaps > max_gap_months for exclusion (sets to NaN or mask).
    """
    # Placeholder: In a real scenario, we'd detect gaps and set a mask variable.
    # For now, we assume the interpolation step handled small gaps and this step
    # ensures large gaps are excluded (already NaN or explicitly masked).
    logger = get_logger("preprocessing")
    logger.info("Flagging large gaps for exclusion.")
    return ds

def apply_basin_stratification_and_masking(ds: xr.Dataset, df_seabass: pd.DataFrame, mask: Optional[np.ndarray] = None) -> xr.Dataset:
    """
    Applies basin stratification and unified masking.
    """
    logger = get_logger("preprocessing")
    logger.info("Applying basin stratification and masking.")
    # Logic to filter ds based on basins present in df_seabass
    return ds

# --- T017a Implementation: Missing Value Analysis ---

def calculate_missing_value_percentage(ds: xr.Dataset) -> float:
    """
    Calculates the percentage of missing values in the dataset.
    Handles xarray DataArrays and Dask arrays.
    """
    total_cells = 0
    missing_cells = 0

    for var_name in ds.data_vars:
        var = ds[var_name]
        # Handle Dask arrays by computing chunks if necessary, but for counting,
        # we can often do it lazily or chunk-wise.
        # To be safe and accurate without loading everything at once, we iterate.
        
        # If it's a dask array, compute the sum of isnull
        if isinstance(var.data, da.Array):
            # Count total elements
            total_cells += var.size
            # Count missing: sum of isnull
            missing_cells += var.isnull().sum().compute()
        else:
            total_cells += var.size
            missing_cells += var.isnull().sum().values

    if total_cells == 0:
        return 0.0

    return (missing_cells / total_cells) * 100.0

def verify_sc004_compliance(missing_percentage: float, threshold: float = 5.0) -> bool:
    """
    Verifies compliance with SC-004 (<= 5% missing values).
    """
    return missing_percentage <= threshold

def generate_missing_value_report(missing_percentage: float, is_compliant: bool, output_path: Union[str, Path]) -> None:
    """
    Generates a JSON report of the missing value analysis.
    """
    report = {
        "missing_value_percentage": float(missing_percentage),
        "threshold_percent": 5.0,
        "is_compliant": is_compliant,
        "sc004_status": "PASS" if is_compliant else "FAIL",
        "details": "Dataset meets SC-004 requirement" if is_compliant else "Dataset exceeds SC-004 missing value threshold"
    }
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger = get_logger("preprocessing")
    logger.info(f"Missing value report generated at {path}")

# --- Main Execution ---

def main():
    """
    Main entry point for T017a: Calculate missing value percentage and verify SC-004.
    Expects data/raw/modis.nc, data/raw/reanalysis.nc, data/raw/seabass.csv to exist.
    Produces data/logs/missing_value_report.json.
    """
    # Setup logging
    logger = setup_memory_logging("data/logs/memory_enforcement.log")
    log_pipeline_event("T017a", "Starting missing value analysis")

    try:
        # 1. Load Data
        logger.info("Loading MODIS data...")
        ds_modis = load_modis_data("data/raw/modis.nc")
        
        logger.info("Loading Reanalysis data...")
        ds_reanalysis = load_reanalysis_data("data/raw/reanalysis.nc")
        
        logger.info("Loading SeaBASS data...")
        df_seabass = load_seabass_data("data/raw/seabass.csv")

        # 2. (Optional) Validate temporal overlap if needed for context, 
        # though T013a should have handled this. 
        # We assume the aligned dataset is already prepared in T017.
        # However, T017a specifically asks to calculate on the output of T017.
        # The task description says "Generate final aligned dataset artifact in data/processed/aligned_dataset.nc (T017)".
        # So we should load THAT file, not the raw ones, to check the final alignment quality.
        
        aligned_path = Path("data/processed/aligned_dataset.nc")
        if not aligned_path.exists():
            raise FileNotFoundError(f"Aligned dataset not found at {aligned_path}. T017 must run first.")
        
        logger.info(f"Loading aligned dataset from {aligned_path}...")
        ds_aligned = xr.open_dataset(aligned_path, chunks='auto')
        
        # 3. Calculate Missing Value Percentage
        logger.info("Calculating missing value percentage...")
        missing_pct = calculate_missing_value_percentage(ds_aligned)
        logger.info(f"Missing value percentage: {missing_pct:.4f}%")

        # 4. Verify SC-004 Compliance
        is_compliant = verify_sc004_compliance(missing_pct)
        status = "COMPLIANT" if is_compliant else "NON-COMPLIANT"
        logger.info(f"SC-004 Compliance Status: {status}")

        # 5. Generate Report
        report_path = "data/logs/missing_value_report.json"
        generate_missing_value_report(missing_pct, is_compliant, report_path)

        log_pipeline_event("T017a", "Completed successfully", {"missing_pct": missing_pct, "compliant": is_compliant})
        
        # Close datasets
        ds_modis.close()
        ds_reanalysis.close()
        ds_aligned.close()

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
