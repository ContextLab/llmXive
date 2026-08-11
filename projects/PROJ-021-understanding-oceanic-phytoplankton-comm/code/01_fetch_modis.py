"""
Fetches MODIS Aqua/Terra ocean color data from the NASA MODIS dataset on HuggingFace.
Saves the result to data/raw/modis.nc.
"""
import os
import sys
import logging
from pathlib import Path
import numpy as np
import xarray as xr

# Ensure the project root is in the path for relative imports if run as a script
# However, the prompt indicates imports like 'from utils.config import ...'
# We assume the runner sets PYTHONPATH or runs from project root.
# We will use absolute imports relative to the project structure as per the API surface.
try:
    from utils.logging_config import get_logger
    from utils.config import get_config
except ImportError:
    # Fallback for direct execution if utils not in path yet, though T002/T004 should exist
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    class FakeConfig:
        @staticmethod
        def get_config():
            return {'ram_limit_gb': 7.0}
    get_config = FakeConfig.get_config

logger = get_logger("01_fetch_modis")

def fetch_modis_data(output_path: Path) -> None:
    """
    Fetches MODIS Aqua/Terra ocean color data and saves it to a NetCDF file.
    
    Args:
        output_path: Path where the resulting .nc file will be saved.
    """
    logger.info(f"Starting MODIS data fetch to {output_path}")
    
    # Verify output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Use the verified source as per task description
        # The task explicitly mentions: datasets.load_dataset("nasa-modis/MODIS-Aqua-Chlorophyll")
        # We assume 'datasets' is installed (T002 requirements)
        from datasets import load_dataset
        
        logger.info("Loading dataset from nasa-modis/MODIS-Aqua-Chlorophyll...")
        
        # Load the dataset. We use streaming to handle potential size issues,
        # but we must materialize it to save as a single NetCDF.
        # If the dataset is too large, we might need to sample, but the task
        # asks for the data. We will attempt to load the full dataset if possible.
        # If it fails due to memory, we will let it crash (fail loudly) as per constraints.
        
        dataset = load_dataset("nasa-modis/MODIS-Aqua-Chlorophyll", split="train", streaming=False)
        
        # Convert to xarray
        # The dataset structure from HF usually has 'image' or similar keys.
        # We need to inspect the features or assume a standard structure for MODIS Chlorophyll.
        # Common structure: 'lat', 'lon', 'time', 'chlorophyll_a'
        
        # Convert to pandas then to xarray for easier manipulation if needed,
        # or directly construct xarray if the dataset is tabular.
        # Assuming the HF dataset is tabular (Arrow format) with coordinates.
        
        df = dataset.to_pandas()
        
        # Check for required columns. If they don't exist, we might need to adapt.
        # Standard MODIS L3/L4 products usually have: time, lat, lon, chlorophyll
        required_cols = ['time', 'lat', 'lon', 'chlorophyll_a']
        missing = [c for c in required_cols if c not in df.columns]
        
        if missing:
            # Fallback: try to find similar columns or raise error
            logger.warning(f"Expected columns {required_cols} not found. Available: {df.columns.tolist()}")
            # Attempt to map common variations
            if 'chlorophyll' in df.columns:
                df['chlorophyll_a'] = df['chlorophyll']
            if 'chlor_a' in df.columns:
                df['chlorophyll_a'] = df['chlor_a']
            
            if 'chlorophyll_a' not in df.columns:
                raise ValueError(f"Could not identify chlorophyll column. Available: {df.columns.tolist()}")
            
            if 'time' not in df.columns:
                if 'datetime' in df.columns:
                    df['time'] = df['datetime']
                elif 'date' in df.columns:
                    df['time'] = df['date']
                else:
                    raise ValueError("Could not identify time column.")
                    
            if 'lat' not in df.columns:
                if 'latitude' in df.columns:
                    df['lat'] = df['latitude']
                else:
                    raise ValueError("Could not identify latitude column.")
                    
            if 'lon' not in df.columns:
                if 'longitude' in df.columns:
                    df['lon'] = df['longitude']
                else:
                    raise ValueError("Could not identify longitude column.")

        # Create xarray dataset
        # We assume the data is already gridded or we need to structure it.
        # If it's point data, we might need to unstack or reshape.
        # For now, we assume it's a 1D list of observations or a 2D grid.
        # Let's try to construct a standard structure: (time, lat, lon)
        
        # If the data is already in a grid format in the dataset, we can use it directly.
        # If not, we might need to pivot.
        # Given the task is "Fetch ... to modis.nc", we will create a valid NetCDF.
        
        # Attempt to create a simple xarray from the dataframe
        # Assuming unique time/lat/lon combinations or a flat list that needs reshaping
        # If the dataset is large, this might be heavy.
        
        # Let's try to convert to xarray directly
        ds = df.set_index(['time', 'lat', 'lon']).to_xarray()
        
        # Ensure chlorophyll_a is the main data variable
        if 'chlorophyll_a' not in ds.data_vars:
            # Try to find the column that holds the value
            val_col = [c for c in df.columns if c not in ['time', 'lat', 'lon']][0]
            ds = df.set_index(['time', 'lat', 'lon'])[val_col].to_xarray()
            ds = ds.rename(val_col, 'chlorophyll_a')
        
        # Add attributes
        ds.attrs['source'] = "nasa-modis/MODIS-Aqua-Chlorophyll"
        ds['chlorophyll_a'].attrs['units'] = 'mg/m^3'
        ds['chlorophyll_a'].attrs['long_name'] = 'Chlorophyll-a concentration'
        
        logger.info(f"Dataset shape: {ds.chunks}")
        logger.info(f"Saving to {output_path}...")
        
        # Save to NetCDF
        ds.to_netcdf(output_path, engine='netcdf4')
        
        logger.info(f"Successfully saved MODIS data to {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to fetch or save MODIS data: {e}", exc_info=True)
        # Fail loudly as per constraints
        raise

def main():
    """Main entry point for the script."""
    config = get_config()
    output_dir = Path("data/raw")
    output_path = output_dir / "modis.nc"
    
    fetch_modis_data(output_path)

if __name__ == "__main__":
    main()
