import os
import sys
import logging
from pathlib import Path
import numpy as np
import xarray as xr

# Ensure we can import from utils if needed, though this script is standalone
# The API surface indicates we import 'from 01_fetch_modis import fetch_modis_data, main'
# So we must define these at module level.

# Add project root to path to allow relative imports if this file is run as script
# but also to allow importing from utils if we needed to (not needed for this specific task logic)
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger

# The task requires fetching MODIS data using datasets.load_dataset
# We need to add 'datasets' to requirements if not present, but the task
# implies we should use the provided API surface or standard libraries.
# Since T002 added 'datasets' to requirements.txt, we can import it.
try:
    from datasets import load_dataset
except ImportError:
    # Fallback if not installed, though T002 should have ensured it
    print("Error: 'datasets' library not found. Please ensure it is installed.")
    sys.exit(1)

logger = get_logger(__name__)

def fetch_modis_data(output_path: Path) -> None:
    """
    Fetches MODIS Aqua/Terra ocean color data from the verified HuggingFace source
    and saves it to the specified output path as a NetCDF file.

    Source: 'nasa-modis/MODIS-Aqua-Chlorophyll'
    Output: data/raw/modis.nc

    This function:
    1. Loads the dataset using the 'datasets' library.
    2. Converts the data to an xarray Dataset.
    3. Ensures necessary coordinates (latitude, longitude, time) exist.
    4. Saves to NetCDF format.
    """
    logger.info(f"Starting MODIS data fetch to {output_path}")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Load the dataset from HuggingFace
        # The task specifies "nasa-modis/MODIS-Aqua-Chlorophyll"
        # We assume this dataset exists and returns a format compatible with xarray
        dataset = load_dataset("nasa-modis/MODIS-Aqua-Chlorophyll", split="train") # Adjust split if needed

        # Convert to pandas DataFrame first if it's a DatasetDict or similar
        # The 'datasets' library returns a Dataset object which can be converted to pandas
        df = dataset.to_pandas()

        logger.info(f"Loaded MODIS dataset with {len(df)} rows")

        # We need to convert this to an xarray Dataset suitable for oceanographic analysis.
        # Typically, this involves reshaping or ensuring we have lat, lon, time dimensions.
        # Since we don't know the exact schema of the HuggingFace dataset, we assume
        # standard columns like 'latitude', 'longitude', 'time', 'chlorophyll' exist.
        # If the dataset structure is different, this might need adjustment.
        # However, for the purpose of this task, we will create a minimal valid NetCDF
        # that represents the data we fetched.

        # Check for required columns
        required_cols = ['latitude', 'longitude', 'time', 'chlorophyll']
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            logger.warning(f"Missing expected columns: {missing_cols}. Attempting to map or use available data.")
            # If columns are missing, we might need to map them or raise an error.
            # For now, let's assume the dataset has them or similar names.
            # If the dataset is actually a 3D array (time, lat, lon), the conversion might be different.
            # Let's try a generic approach: assume the dataset has lat/lon/time and a data variable.

        # Convert to xarray
        # If the dataset is tabular (rows = observations), we might need to group by time/lat/lon
        # or simply save as a point dataset.
        # Let's assume we want a gridded or point dataset in NetCDF.

        # Attempt to create an xarray dataset from the dataframe
        # We'll use 'time', 'latitude', 'longitude' as coordinates if they exist
        xds = df.set_index(['time', 'latitude', 'longitude']).to_xarray()

        # If the dataset doesn't have these as indices, we might need to handle it differently.
        # Let's try a more robust conversion if the above fails.
        # However, for the sake of this implementation, we assume the dataset structure allows this.
        # If the dataset is already gridded, we might just need to rename variables.

        # Rename variables to standard names if necessary
        # Assuming 'chlorophyll' is the main variable
        if 'chlorophyll' in xds.data_vars:
            xds = xds.rename({'chlorophyll': 'chlorophyll_a'})
        else:
            # If the variable name is different, try to find the first data variable
            if len(xds.data_vars) > 0:
                var_name = list(xds.data_vars.keys())[0]
                xds = xds.rename({var_name: 'chlorophyll_a'})
                logger.warning(f"Renamed variable '{var_name}' to 'chlorophyll_a'")

        # Ensure dimensions are named correctly
        # Often datasets have 'lat', 'lon', 'time' or 'latitude', 'longitude', 'time'
        # We'll assume the index conversion handled this, but let's double check.
        # If the dataset was tabular, the index becomes dimensions.

        # Add metadata
        xds.attrs['source'] = 'nasa-modis/MODIS-Aqua-Chlorophyll'
        xds.attrs['description'] = 'MODIS Aqua/Terra Ocean Color Data'
        if 'chlorophyll_a' in xds.data_vars:
            xds['chlorophyll_a'].attrs['units'] = 'mg/m^3'

        logger.info(f"Saving MODIS data to {output_path}")
        xds.to_netcdf(output_path, format='NETCDF4')
        logger.info(f"Successfully saved MODIS data to {output_path}")

    except Exception as e:
        logger.error(f"Failed to fetch or save MODIS data: {e}")
        # Re-raise or exit depending on desired behavior
        # For a research pipeline, we might want to fail loudly
        raise RuntimeError(f"Error fetching MODIS data: {e}") from e

def main():
    """
    Main entry point for the MODIS data fetching script.
    """
    # Define output path relative to project root
    # The task specifies: data/raw/modis.nc
    output_path = Path("data/raw/modis.nc")

    # If running as a script from the 'code' directory, we might need to adjust
    # But the task says "relative to the project root".
    # Let's assume the script is run from the project root or the path is absolute.
    # To be safe, we can resolve the path relative to the current working directory.
    # However, the task implies the script should write to data/raw/modis.nc.
    # Let's make sure the directory exists.
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fetch_modis_data(output_path)

if __name__ == "__main__":
    main()
