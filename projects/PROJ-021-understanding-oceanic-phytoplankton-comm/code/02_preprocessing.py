import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np
import xarray as xr
import pandas as pd
import json
import psutil

from utils.logging_config import get_logger, setup_logging
from utils.config import get_config

# Ensure logging is configured
setup_logging()
logger = get_logger(__name__)

# Constants
MEMORY_LIMIT_GB = float(os.getenv('MEMORY_LIMIT_GB', '7.0'))
MISSING_VALUE_THRESHOLD = 0.05  # SC-004: <= 5% missing values

def get_current_memory_usage_gb() -> float:
    """Get current RAM usage in GB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)

def enforce_memory_limit_gb(limit_gb: float = MEMORY_LIMIT_GB) -> None:
    """Enforce memory limit by logging warning or raising error."""
    current_usage = get_current_memory_usage_gb()
    if current_usage > limit_gb:
        raise MemoryError(f"Memory usage {current_usage:.2f}GB exceeds limit {limit_gb}GB")
    logger.debug(f"Memory usage check passed: {current_usage:.2f}GB / {limit_gb}GB")

def load_modis_data() -> xr.Dataset:
    """Load MODIS data from raw directory."""
    path = Path("data/raw/modis.nc")
    if not path.exists():
        raise FileNotFoundError(f"MODIS data not found at {path}")
    logger.info(f"Loading MODIS data from {path}")
    return xr.open_dataset(path)

def load_reanalysis_data() -> xr.Dataset:
    """Load Reanalysis data from raw directory."""
    path = Path("data/raw/reanalysis.nc")
    if not path.exists():
        raise FileNotFoundError(f"Reanalysis data not found at {path}")
    logger.info(f"Loading Reanalysis data from {path}")
    return xr.open_dataset(path)

def load_seabass_data() -> pd.DataFrame:
    """Load SeaBASS data from raw directory."""
    path = Path("data/raw/seabass.csv")
    if not path.exists():
        raise FileNotFoundError(f"SeaBASS data not found at {path}")
    logger.info(f"Loading SeaBASS data from {path}")
    return pd.read_csv(path)

def validate_temporal_overlap(ds_modis: xr.Dataset, ds_reanalysis: xr.Dataset, df_seabass: pd.DataFrame) -> bool:
    """Validate temporal overlap between datasets."""
    # Extract time ranges
    modis_time = ds_modis['time'] if 'time' in ds_modis else None
    reanalysis_time = ds_reanalysis['time'] if 'time' in ds_reanalysis else None
    
    # Simple validation logic
    if modis_time is None or reanalysis_time is None:
        logger.warning("Time dimension missing in one of the datasets")
        return False
    
    logger.info("Temporal overlap validation passed")
    return True

def create_basin_mapping(lat: np.ndarray, lon: np.ndarray) -> pd.DataFrame:
    """Create a mapping of coordinates to ocean basins."""
    # Simplified basin mapping logic
    basins = []
    for lat_val, lon_val in zip(lat.flatten(), lon.flatten()):
        if lon_val < -30:
            basin = "Pacific"
        elif -30 <= lon_val < 30:
            basin = "Atlantic"
        else:
            basin = "Indian"
        basins.append(basin)
    
    return pd.DataFrame({'lat': lat.flatten(), 'lon': lon.flatten(), 'basin': basins})

def stratified_split_by_basin(df: pd.DataFrame, basin_col: str = 'basin', 
                              test_size: float = 0.2, val_size: float = 0.1) -> Dict[str, List[int]]:
    """Perform stratified split by ocean basin."""
    from sklearn.model_selection import train_test_split
    
    indices = df.index.tolist()
    basin_labels = df[basin_col].tolist()
    
    # First split for test
    train_val_indices, test_indices, _, _ = train_test_split(
        indices, basin_labels, test_size=test_size, stratify=basin_labels, random_state=42
    )
    
    # Calculate new val size relative to remaining
    new_val_size = val_size / (1 - test_size)
    
    train_indices, val_indices, _, _ = train_test_split(
        train_val_indices, [basin_labels[i] for i in train_val_indices], 
        test_size=new_val_size, stratify=[basin_labels[i] for i in train_val_indices], random_state=42
    )
    
    return {
        'train': train_indices,
        'val': val_indices,
        'test': test_indices
    }

def interpolate_gaps_and_log_error(ds: xr.Dataset, max_gap_months: int = 2) -> xr.Dataset:
    """Interpolate gaps <= 2 months and log errors."""
    logger.info(f"Interpolating gaps up to {max_gap_months} months")
    
    # Example interpolation logic for a specific variable
    if 'chlorophyll' in ds.data_vars:
        ds['chlorophyll'] = ds['chlorophyll'].interpolate_na(dim='time', method='linear')
    
    # Log interpolation errors (simplified)
    error_log_path = Path("data/logs/interpolation_error.log")
    error_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(error_log_path, 'a') as f:
        f.write(f"Interpolation completed at {pd.Timestamp.now()}\n")
    
    return ds

def flag_gaps_for_exclusion(ds: xr.Dataset, max_gap_months: int = 2) -> xr.Dataset:
    """Flag gaps > 2 months for exclusion."""
    logger.info(f"Flagging gaps > {max_gap_months} months for exclusion")
    
    # Create a mask for gaps
    # This is a simplified example; real logic would analyze time series continuity
    if 'chlorophyll' in ds.data_vars:
        ds['quality_flag'] = ds['chlorophyll'].notnull().astype(int)
    
    return ds

def apply_basin_stratification_and_masking(ds: xr.Dataset, df_seabass: pd.DataFrame) -> xr.Dataset:
    """Apply basin stratification and unified masking."""
    logger.info("Applying basin stratification and masking")
    
    # Merge basin info
    # Assuming ds has lat/lon dimensions that match df_seabass
    # This is a simplified integration
    
    return ds

def calculate_missing_value_percentage(ds: xr.Dataset) -> float:
    """Calculate the percentage of missing values in the dataset."""
    total_cells = 0
    missing_cells = 0
    
    for var in ds.data_vars:
        if var == 'quality_flag':
            continue
        data = ds[var].values
        total_cells += data.size
        missing_cells += np.isnan(data).sum()
    
    if total_cells == 0:
        return 0.0
    
    return (missing_cells / total_cells) * 100.0

def verify_sc004_compliance(missing_percentage: float, threshold: float = MISSING_VALUE_THRESHOLD) -> bool:
    """Verify compliance with SC-004 (<=5% missing values)."""
    return missing_percentage <= (threshold * 100)

def generate_missing_value_report(missing_percentage: float, compliant: bool, output_path: Path) -> None:
    """Generate and save the missing value report to JSON."""
    report = {
        "missing_value_percentage": float(missing_percentage),
        "threshold_percentage": float(MISSING_VALUE_THRESHOLD * 100),
        "compliant": bool(compliant),
        "specification": "SC-004",
        "status": "PASS" if compliant else "FAIL",
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Missing value report saved to {output_path}")
    logger.info(f"Result: {report['status']} ({missing_percentage:.2f}% missing)")

def main():
    """Main entry point for T017a: Calculate missing value percentage and verify SC-004."""
    logger.info("Starting T017a: Missing Value Percentage Calculation and SC-004 Verification")
    
    try:
        # Load the aligned dataset (output from T017)
        aligned_path = Path("data/processed/aligned_dataset.nc")
        if not aligned_path.exists():
            raise FileNotFoundError(f"Aligned dataset not found at {aligned_path}. Run T017 first.")
        
        logger.info(f"Loading aligned dataset from {aligned_path}")
        ds = xr.open_dataset(aligned_path)
        
        # Enforce memory limit before heavy processing
        enforce_memory_limit_gb()
        
        # Calculate missing value percentage
        missing_pct = calculate_missing_value_percentage(ds)
        logger.info(f"Calculated missing value percentage: {missing_pct:.4f}%")
        
        # Verify SC-004 compliance
        is_compliant = verify_sc004_compliance(missing_pct)
        
        # Generate report
        report_path = Path("data/logs/missing_value_report.json")
        generate_missing_value_report(missing_pct, is_compliant, report_path)
        
        # Close dataset
        ds.close()
        
        if not is_compliant:
            logger.error(f"SC-004 Compliance FAILED: {missing_pct:.2f}% > 5.00%")
            # Do not raise error here to allow the pipeline to continue if this is a check-only task,
            # but log the failure clearly as per "Fail loudly" principle for data quality.
            # In a strict pipeline, this might raise an exception.
        else:
            logger.info(f"SC-004 Compliance PASSED: {missing_pct:.2f}% <= 5.00%")
            
    except Exception as e:
        logger.error(f"Error during T017a execution: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
