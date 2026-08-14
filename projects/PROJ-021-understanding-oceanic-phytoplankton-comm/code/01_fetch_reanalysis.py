"""
Task T011a: Fetch NOAA/Copernicus Reanalysis data (Temperature, Salinity, Nutrients).

Source: Copernicus Marine Service (CMEMS) via the 'copernicusmarine' Python package.
Dataset: Global Ocean Physics Reanalysis (GLOBAL_REANALYSIS_PHYS_001_030)
Variables: temperature, salinity
Note: Nutrients (nitrate, phosphate) are in the BIO reanalysis. To keep this task 
focused on a single fetch as per the specific "Reanalysis" description (often implying 
physical reanalysis), we fetch the Physical Reanalysis. 
If nutrients are strictly required in this specific file, the dataset would need to 
be switched to GLOBAL_REANALYSIS_BIO_001_030, but that lacks Temperature/Salinity 
at the same native resolution in a single fetch without merging. 

However, the task asks for "Temperature, Salinity, Nutrients". 
The most robust single-source approach for a unified NetCDF is the Physical Reanalysis 
for T/S and the Bio Reanalysis for Nutrients. Since the task implies a single output 
file `data/raw/reanalysis.nc`, we will fetch the Physical Reanalysis (T, S) and 
attempt to fetch Nutrients from the Bio reanalysis if available in a compatible 
subset, OR we will fetch the Physical Reanalysis which is the primary "Reanalysis" 
for ocean physics. 

Given the strict constraint "NO synthetic fallback" and "fail loudly", we will 
implement a fetch for the Global Ocean Physics Reanalysis which provides Temperature 
and Salinity. For Nutrients, we will fetch the Global Ocean Biogeochemistry Reanalysis 
and merge them if dimensions align, or raise an error if the merge is impossible 
within the time/memory budget. 

To ensure the task is completable within the compute budget and avoids complex 
multi-dataset merging logic that might fail, we will prioritize the Physical Reanalysis 
(T, S) which is the standard "Reanalysis" product. If the spec strictly demands 
Nutrients in the same file, we will add the BIO variables from the BIO reanalysis 
dataset. 

We will use the `copernicusmarine` package. 
Dataset ID: cmems_mod_glo_phy_my_0.083deg_P1D-m (Physical)
Dataset ID: cmems_mod_glo_bio_my_0.25deg_P1D-m (Biogeochemical - for nutrients)

Strategy: 
1. Fetch Physical Reanalysis (T, S) for a global subset (e.g., 1 year to keep it manageable 
   for the "raw" stage, or a specific region if specified. The task doesn't specify region, 
   so we fetch a global subset for a recent year to ensure the file exists and is valid).
2. Fetch Biogeochemical Reanalysis (Nitrate, Phosphate) for the same time/region.
3. Merge into a single NetCDF.

If authentication is required (which it is for CMEMS), the script will fail loudly 
if credentials are not found in the environment or .netrc.
"""
import os
import sys
import logging
from pathlib import Path
import xarray as xr
import numpy as np

# Ensure we can import from the project utils
sys.path.insert(0, str(Path(__file__).parent))
from utils.config import get_config
from utils.logging_config import get_logger
from utils.data_loaders import get_available_ram_gb

logger = get_logger(__name__)
config = get_config()

def fetch_reanalysis_data(output_path: str):
    """
    Fetches NOAA/Copernicus Reanalysis data (Temperature, Salinity, Nutrients).
    Writes to `output_path`.
    """
    logger.info(f"Starting fetch of Reanalysis data to {output_path}")
    
    # Check for Copernicus credentials
    username = os.environ.get("CMEMS_USERNAME")
    password = os.environ.get("CMEMS_PASSWORD")
    
    if not username or not password:
        logger.error("CMEMS_USERNAME and CMEMS_PASSWORD environment variables are not set.")
        logger.error("Please set them to access Copernicus Marine Service data.")
        raise RuntimeError("Missing CMEMS credentials. Cannot fetch real data.")

    # Define datasets
    # Physical Reanalysis (Temperature, Salinity)
    # Dataset: GLOBAL_REANALYSIS_PHYS_001_030
    # Variable: temperature, salinity
    physical_dataset_id = "cmems_mod_glo_phy_my_0.083deg_P1D-m"
    
    # Biogeochemical Reanalysis (Nutrients: nitrate, phosphate)
    # Dataset: GLOBAL_REANALYSIS_BIO_001_030
    # Variable: nitrate, phosphate
    bio_dataset_id = "cmems_mod_glo_bio_my_0.25deg_P1D-m"

    # Define temporal and spatial subset to ensure the script runs within 
    # reasonable time and memory limits for the "raw" fetch stage.
    # We fetch one year of data (2022) and a global subset (or full global if fast).
    # To be safe on memory, we fetch a specific region or a shorter time if needed.
    # Let's fetch 2022 data for a mid-latitude band to ensure we get valid data
    # and keep the file size manageable for the "raw" stage.
    # However, the task implies a global dataset. We will fetch a global subset 
    # for 1 month to ensure the pipeline can run, or 1 year if the network allows.
    # Given the "fail loudly" constraint, we will attempt to fetch a manageable 
    # chunk (e.g., 1 month) to guarantee the file is created and valid.
    # If the user needs the full dataset, they can adjust the time range.
    
    time_start = "2022-06-01"
    time_end = "2022-07-01"
    longitude_min = -180
    longitude_max = 180
    latitude_min = -60
    latitude_max = 60

    try:
        # Import copernicusmarine here to avoid hard dependency if not needed,
        # but the task requires real data, so it must be installed.
        import copernicusmarine
        from copernicusmarine import subset

        # Fetch Physical Data
        logger.info(f"Fetching Physical Reanalysis (T, S) from {physical_dataset_id}...")
        physical_output = subset(
            dataset_id=physical_dataset_id,
            variables=["temperature", "salinity"],
            minimum_longitude=longitude_min,
            maximum_longitude=longitude_max,
            minimum_latitude=latitude_min,
            maximum_latitude=latitude_max,
            start_datetime=time_start,
            end_datetime=time_end,
            output_directory=str(Path(output_path).parent),
            output_filename="temp_reanalysis.nc",
            credentials_username=username,
            credentials_password=password,
            # Use a smaller chunk size if available, or default
            force_download=False
        )
        
        # Fetch Bio Data
        logger.info(f"Fetching Biogeochemical Reanalysis (Nutrients) from {bio_dataset_id}...")
        bio_output = subset(
            dataset_id=bio_dataset_id,
            variables=["nitrate", "phosphate"],
            minimum_longitude=longitude_min,
            maximum_longitude=longitude_max,
            minimum_latitude=latitude_min,
            maximum_latitude=latitude_max,
            start_datetime=time_start,
            end_datetime=time_end,
            output_directory=str(Path(output_path).parent),
            output_filename="bio_reanalysis.nc",
            credentials_username=username,
            credentials_password=password,
            force_download=False
        )

        # Load and Merge
        logger.info("Loading fetched NetCDF files for merging...")
        ds_phy = xr.open_dataset(physical_output[0])
        ds_bio = xr.open_dataset(bio_output[0])

        # Align dimensions if necessary (Bio might be coarser)
        # We will regrid bio to phy or vice versa. Let's regrid bio to phy's grid 
        # if the resolution difference is significant, or just merge if they align.
        # For this task, we assume the merge is possible. If dimensions mismatch,
        # we will use xarray's reindex or interp.
        
        # Check dimensions
        logger.info(f"Physical dims: {ds_phy.dims}")
        logger.info(f"Bio dims: {ds_bio.dims}")

        # If dimensions differ, we need to interpolate.
        # Bio is 0.25deg, Phy is 0.083deg. We will interpolate Bio to Phy grid.
        if "longitude" in ds_bio and "longitude" in ds_phy:
            logger.info("Interpolating Bio data to Physical grid...")
            ds_bio_interp = ds_bio.interp(
                longitude=ds_phy.longitude.values,
                latitude=ds_phy.latitude.values,
                method="linear"
            )
            # Drop non-interpolated variables if any
            ds_merged = xr.merge([ds_phy, ds_bio_interp], compat="override")
        else:
            # Fallback: just merge if dimensions align perfectly
            ds_merged = xr.merge([ds_phy, ds_bio])

        # Save merged dataset
        logger.info(f"Saving merged dataset to {output_path}")
        ds_merged.to_netcdf(output_path, encoding={
            "temperature": {"dtype": "float32"},
            "salinity": {"dtype": "float32"},
            "nitrate": {"dtype": "float32"},
            "phosphate": {"dtype": "float32"}
        })
        
        # Close datasets
        ds_phy.close()
        ds_bio.close()
        if "ds_bio_interp" in locals():
            ds_bio_interp.close()
        ds_merged.close()

        logger.info(f"Successfully fetched and saved Reanalysis data to {output_path}")
        return True

    except ImportError:
        logger.error("The 'copernicusmarine' package is not installed.")
        logger.error("Please install it: pip install copernicusmarine")
        raise
    except Exception as e:
        logger.error(f"Failed to fetch or process reanalysis data: {str(e)}")
        raise

def main():
    """Main entry point for T011a."""
    # Ensure output directory exists
    output_path = "data/raw/reanalysis.nc"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    try:
        fetch_reanalysis_data(output_path)
        logger.info("Task T011a completed successfully.")
    except Exception as e:
        logger.critical(f"Task T011a failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
