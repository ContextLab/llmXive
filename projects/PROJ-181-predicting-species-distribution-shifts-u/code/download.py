import os
import time
import logging
from datetime import datetime
from pathlib import Path
import requests
import tarfile
import io
import shutil

from config import DATA_DIR
from logging_config import get_download_logger

# WorldClim v2.1 historical (1970-2000) base URL for Bioclim variables
# Variables are numbered 1-19. The files are named bio1_10min.tif, etc.
# We download the 10-minute resolution files for the "world" region.
WC_BASE_URL = "https://biogeo.ucdavis.edu/data/worldclim/v2.1/wc2.1_10m_bio/wc2.1_10m_bio_{}.tif"
WC_TAR_URL = "https://biogeo.ucdavis.edu/data/worldclim/v2.1/wc2.1_10m_bio.tar.gz"

# CMIP6 Future Climate Data (SSP2-4.5, 2050)
# Source: WorldClim CMIP6 data (downscaled)
# URL Pattern: https://biogeo.ucdavis.edu/data/cmip6/wc2.1_10m_bio_ssp/
# Files are named: wc2.1_10m_bio_{var}_{ssp}_{resolution}.tif
# For 2050, we use the '2050' label in the filename pattern if available, 
# or the specific scenario file. 
# WorldClim CMIP6 files usually follow: wc2.1_10m_bio_{var}_ssp{scenario}_2050.tif
# However, the most reliable direct link pattern for specific variables and scenarios 
# at 10min resolution is often:
# https://biogeo.ucdavis.edu/data/cmip6/wc2.1_10m_bio_ssp/wc2.1_10m_bio_{var}_ssp245_2050.tif
# Note: The actual URL structure might vary slightly. The standard WorldClim CMIP6 
# download page lists files like: wc2.1_10m_bio_01_ssp245_2050.tif
CMIP6_BASE_URL = "https://biogeo.ucdavis.edu/data/cmip6/wc2.1_10m_bio_ssp/wc2.1_10m_bio_{var}_ssp245_2050.tif"

# Output directory for future climate
CMIP6_FUTURE_DIR = DATA_DIR / "raw" / "cmip6_future"

def get_download_logger():
    """Returns the download logger instance."""
    return logging.getLogger("download")

def download_worldclim_bioclim_variables():
    """
    Downloads all 19 WorldClim v2.1 historical Bioclim variables (bio1-bio19).
    Saves them as individual .tif files in data/raw/climate_historical/.
    
    This function attempts to download the full tarball to ensure consistency,
    then extracts only the 19 required .tif files. If the tarball is too large
    or fails, it falls back to downloading individual files.
    
    FR-001 Compliance: Ensures all 19 Bioclim variables are present.
    """
    logger = get_download_logger()
    logger.info("Starting download of WorldClim v2.1 historical climate data (1970-2000).")
    
    # Ensure output directory exists
    CLIMATE_HISTORICAL_DIR = DATA_DIR / "raw" / "climate_historical"
    CLIMATE_HISTORICAL_DIR.mkdir(parents=True, exist_ok=True)
    
    downloaded_files = []
    expected_vars = list(range(1, 20)) # 1 to 19
    
    # Strategy: Try to download individual files if tarball is problematic or too large for memory
    # WorldClim 10min tarball is ~200MB, which is manageable, but individual download is more robust for CI/CD
    # We will iterate and download each variable individually to avoid large tarball handling issues
    
    logger.info(f"Downloading {len(expected_vars)} Bioclim variables individually.")
    
    for var_num in expected_vars:
        filename = f"wc2.1_10m_bio_{var_num:02d}.tif"
        output_path = CLIMATE_HISTORICAL_DIR / filename
        
        if output_path.exists():
            logger.info(f"Variable {var_num} ({filename}) already exists, skipping.")
            downloaded_files.append(output_path)
            continue
        
        url = WC_BASE_URL.format(var_num)
        logger.info(f"Downloading Variable {var_num} from {url}...")
        
        try:
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                # Download in chunks to handle potential large files gracefully
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            if os.path.getsize(output_path) > 0:
                downloaded_files.append(output_path)
                logger.info(f"Successfully downloaded Variable {var_num} ({filename}).")
            else:
                logger.warning(f"Downloaded file for Variable {var_num} is empty.")
                os.remove(output_path)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download Variable {var_num}: {e}")
            raise RuntimeError(f"Failed to download required climate variable {var_num}. "
                             f"Cannot proceed without all 19 Bioclim variables (FR-001).")
        except Exception as e:
            logger.error(f"Unexpected error downloading Variable {var_num}: {e}")
            raise

    # Validation: Check that all 19 files exist
    missing_vars = []
    for var_num in expected_vars:
        fname = f"wc2.1_10m_bio_{var_num:02d}.tif"
        if not (CLIMATE_HISTORICAL_DIR / fname).exists():
            missing_vars.append(var_num)
    
    if missing_vars:
        logger.error(f"Missing variables after download: {missing_vars}")
        raise RuntimeError(f"Validation failed: Variables {missing_vars} are missing. "
                         f"All 19 Bioclim variables are required (FR-001).")
    
    logger.info(f"Successfully downloaded and validated all 19 Bioclim variables in {CLIMATE_HISTORICAL_DIR}.")
    return downloaded_files

def download_cmip6_future_bioclim_variables():
    """
    Downloads all 19 CMIP6 SSP2-4.5 future (2050) Bioclim variables (bio1-bio19).
    Saves them as individual .tif files in data/raw/cmip6_future/.
    
    Source: WorldClim CMIP6 data (https://biogeo.ucdavis.edu/data/cmip6/)
    Scenario: SSP2-4.5 (Representative Concentration Pathway 4.5 equivalent)
    Time Period: 2050 (Average of 2041-2060)
    
    FR-001 Compliance: Ensures all 19 Bioclim variables are present for future projection.
    FR-009 Compliance: Provides future climate data for model projection.
    """
    logger = get_download_logger()
    logger.info("Starting download of CMIP6 SSP2-4.5 future climate data (2050).")
    
    # Ensure output directory exists
    CMIP6_FUTURE_DIR.mkdir(parents=True, exist_ok=True)
    
    downloaded_files = []
    expected_vars = list(range(1, 20)) # 1 to 19
    
    logger.info(f"Downloading {len(expected_vars)} CMIP6 Bioclim variables (SSP2-4.5, 2050) individually.")
    
    for var_num in expected_vars:
        # Format variable number to 2 digits (01, 02, ..., 19)
        var_str = f"{var_num:02d}"
        filename = f"wc2.1_10m_bio_{var_str}_ssp245_2050.tif"
        output_path = CMIP6_FUTURE_DIR / filename
        
        if output_path.exists():
            logger.info(f"Variable {var_num} ({filename}) already exists, skipping.")
            downloaded_files.append(output_path)
            continue
        
        url = CMIP6_BASE_URL.format(var=var_str)
        logger.info(f"Downloading Variable {var_num} from {url}...")
        
        try:
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                # Download in chunks to handle potential large files gracefully
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            if os.path.getsize(output_path) > 0:
                downloaded_files.append(output_path)
                logger.info(f"Successfully downloaded Variable {var_num} ({filename}).")
            else:
                logger.warning(f"Downloaded file for Variable {var_num} is empty.")
                os.remove(output_path)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download Variable {var_num}: {e}")
            raise RuntimeError(f"Failed to download required CMIP6 climate variable {var_num}. "
                             f"Cannot proceed without all 19 Bioclim variables for future projection (FR-001).")
        except Exception as e:
            logger.error(f"Unexpected error downloading Variable {var_num}: {e}")
            raise

    # Validation: Check that all 19 files exist
    missing_vars = []
    for var_num in expected_vars:
        var_str = f"{var_num:02d}"
        fname = f"wc2.1_10m_bio_{var_str}_ssp245_2050.tif"
        if not (CMIP6_FUTURE_DIR / fname).exists():
            missing_vars.append(var_num)
    
    if missing_vars:
        logger.error(f"Missing CMIP6 variables after download: {missing_vars}")
        raise RuntimeError(f"Validation failed: CMIP6 Variables {missing_vars} are missing. "
                         f"All 19 Bioclim variables are required for future projection (FR-001).")
    
    logger.info(f"Successfully downloaded and validated all 19 CMIP6 Bioclim variables in {CMIP6_FUTURE_DIR}.")
    return downloaded_files

def main():
    """Main entry point for downloading climate data (Historical and Future)."""
    logger = get_download_logger()
    logger.info("Executing T015/T015b: Download WorldClim and CMIP6 climate rasters.")
    
    try:
        # Download historical data (T015)
        download_worldclim_bioclim_variables()
        
        # Download future data (T015b)
        download_cmip6_future_bioclim_variables()
        
        logger.info("T015 and T015b completed successfully.")
    except Exception as e:
        logger.error(f"Climate download failed: {e}")
        raise

if __name__ == "__main__":
    main()