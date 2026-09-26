import os
import sys
import csv
import hashlib
import logging
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml

# Import from project modules based on API surface
from config import Config
from utils import setup_logging
from state_manager import update_artifact

# Project root relative to this file (assumed code/ directory)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
STATE_FILE = PROJECT_ROOT / "state" / "projects" / "PROJ-334-predicting-avian-song-variation-with-cli.yaml"
CHECKSUMS_FILE = DATA_DIR / "checksums.txt"
CONTRACTS_FILE = PROJECT_ROOT / "contracts" / "data_sources.yaml"

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_checksums_file(file_path: Path, file_hash: str, logger: logging.Logger) -> None:
    """Append file hash to checksums.txt."""
    checksums_file = CHECKSUMS_FILE
    if not checksums_file.exists():
        checksums_file.parent.mkdir(parents=True, exist_ok=True)
        with open(checksums_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['filename', 'hash'])
    
    with open(checksums_file, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([file_path.name, file_hash])
    logger.info(f"Updated checksums.txt with {file_path.name}")

def download_file(url: str, output_path: Path, logger: logging.Logger) -> bool:
    """Download a file from URL with streaming."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        logger.info(f"Downloaded {url} to {output_path}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        return False

def fetch_worldclim_data(logger: logging.Logger) -> Optional[Path]:
    """
    Download real climate variables from WorldClim v2.1.
    
    WorldClim v2.1 provides global climate data at 30 arc-second resolution (~1km).
    We download the global monthly temperature and precipitation files.
    Since the dataset is large, we download the specific global files needed:
    - tavg: monthly mean temperature (bioclim variable 1 is annual mean, but we need monthly to derive or use directly)
    - prec: monthly precipitation
    - elev: elevation (from WorldClim v2.1 elevation)
    
    Note: WorldClim v2.1 files are typically named like:
    wc2.1_30s_tavg.zip, wc2.1_30s_prec.zip, wc2.1_30s_elev.zip
    We will download the global zip files, extract the specific monthly rasters,
    and convert them to a CSV format for analysis.
    
    However, for the purpose of this task and to avoid massive unzipping in a single script,
    we will download the global aggregated files or a representative sample if the full
    dataset is too large for immediate processing. 
    
    Given the constraint "streaming=True or itertools.islice" and "large dataset",
    and the fact that WorldClim is raster data, we will:
    1. Download the global monthly temperature (tavg) and precipitation (prec) and elevation (elev) rasters.
    2. Since processing all global rasters into a CSV is heavy, we will download the files,
       and then sample points or process a subset if the full dataset is too large.
       BUT the task says "abort on fetch failure" and "real data".
    
    Strategy:
    - Download the global zip files for tavg, prec, elev.
    - Extract them.
    - Since we need to produce a CSV of climate snapshots (lat, lon, temp, precip, elev),
      we will iterate through the rasters. 
    
    To satisfy "streaming" and "large dataset" without crashing memory:
    We will download the files, then process them in chunks (month by month) and write
    to the CSV incrementally.
    
    URLs (WorldClim v2.1):
    - Temp: https://worldclim.org/data/v2.1/worldclim2.1.html
    - Direct links for global monthly:
      - tavg: https://biogeo.ucdavis.edu/data/worldclim/v2.1/global/tif/wc2.1_30s_tavg.zip
      - prec: https://biogeo.ucdavis.edu/data/worldclim/v2.1/global/tif/wc2.1_30s_prec.zip
      - elev: https://biogeo.ucdavis.edu/data/worldclim/v2.1/global/tif/wc2.1_30s_elev.zip
    
    We will download these, extract, and process.
    """
    
    # Load data sources contract to get URLs
    try:
        with open(CONTRACTS_FILE, 'r') as f:
            sources = yaml.safe_load(f)
        worldclim_info = sources.get('worldclim', {})
        urls = worldclim_info.get('urls', {})
    except Exception as e:
        logger.error(f"Could not load data sources contract: {e}")
        return None

    # Define URLs based on standard WorldClim v2.1 structure if not in contract
    # Fallback to standard URLs if contract doesn't specify exact zip links
    base_url = "https://biogeo.ucdavis.edu/data/worldclim/v2.1/global/tif"
    if 'tavg_zip' not in urls:
        urls['tavg_zip'] = f"{base_url}/wc2.1_30s_tavg.zip"
    if 'prec_zip' not in urls:
        urls['prec_zip'] = f"{base_url}/wc2.1_30s_prec.zip"
    if 'elev_zip' not in urls:
        urls['elev_zip'] = f"{base_url}/wc2.1_30s_elev.zip"

    # Download files
    tavg_zip = RAW_DIR / "wc2.1_30s_tavg.zip"
    prec_zip = RAW_DIR / "wc2.1_30s_prec.zip"
    elev_zip = RAW_DIR / "wc2.1_30s_elev.zip"

    if not download_file(urls['tavg_zip'], tavg_zip, logger):
        logger.error("Failed to download temperature data. Aborting.")
        return None
    if not download_file(urls['prec_zip'], prec_zip, logger):
        logger.error("Failed to download precipitation data. Aborting.")
        return None
    if not download_file(urls['elev_zip'], elev_zip, logger):
        logger.error("Failed to download elevation data. Aborting.")
        return None

    # Record checksums for downloaded files
    for f in [tavg_zip, prec_zip, elev_zip]:
        h = calculate_sha256(f)
        update_checksums_file(f, h, logger)
        update_artifact(STATE_FILE, f.name, h)

    # Extract and process
    # We need to extract the zips. Since we cannot use external heavy dependencies like rasterio
    # in this specific script without ensuring they are installed (they are in requirements),
    # we will use zipfile.
    import zipfile
    import numpy as np
    from pathlib import Path

    # Extract to a temporary directory
    extract_dir = RAW_DIR / "worldclim_extracted"
    extract_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Extracting files...")
    for zip_file in [tavg_zip, prec_zip, elev_zip]:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

    # Now we have .tif files. We need to convert to CSV.
    # Since the full global dataset is huge (~10k x 10k pixels), we cannot load it all into memory.
    # We will use a sampling strategy or process in chunks if we had a way to stream rasters.
    # However, the task says "streaming=True" for fetching. For processing, we must handle the size.
    # We will sample a subset of the global grid to create the CSV, OR process the whole thing
    # if we can do it efficiently.
    # Given the constraint "Large dataset? Stream the real data", we will iterate over the rasters
    # and sample points.
    
    # We need to identify the files.
    # tavg files: wc2.1_30s_tavg_1.tif, ... wc2.1_30s_tavg_12.tif
    # prec files: wc2.1_30s_prec_1.tif, ... wc2.1_30s_prec_12.tif
    # elev files: wc2.1_30s_elev.tif (single file)
    
    tavg_files = sorted(extract_dir.glob("wc2.1_30s_tavg_*.tif"))
    prec_files = sorted(extract_dir.glob("wc2.1_30s_prec_*.tif"))
    elev_file = extract_dir / "wc2.1_30s_elev.tif"

    if not tavg_files or not prec_files or not elev_file.exists():
        logger.error("Extracted files not found as expected.")
        return None

    # We will use rasterio to read the rasters. It is in requirements.
    try:
        import rasterio
        from rasterio.transform import xy
    except ImportError:
        logger.error("rasterio is required but not installed.")
        return None

    # Output file
    output_csv = RAW_DIR / "worldclim_climate_snapshots.csv"
    
    # We will sample 10,000 random points from the global grid to keep the CSV manageable
    # while still representing the real data distribution.
    # If we tried to write all ~10^8 pixels, it would be too large.
    # The task says "Large dataset? Stream the real data... or use a well-defined REAL sample".
    # We will use a sample of 50,000 points.
    
    sample_size = 50000
    logger.info(f"Sampling {sample_size} points from global rasters...")
    
    # Read one tiff to get grid info
    with rasterio.open(tavg_files[0]) as src:
        height, width = src.height, src.width
        transform = src.transform
        crs = src.crs

    # Generate random indices
    rng = np.random.default_rng(42)
    indices = rng.integers(0, height * width, size=sample_size)
    rows = indices // width
    cols = indices % width

    # Prepare CSV writer
    with open(output_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['lat', 'lon', 'temperature', 'precipitation', 'elevation', 'month'])

        # We need to sample from all 12 months? Or average?
        # The task asks for "temperature, precipitation, elevation".
        # We will pick a random month for each point to keep the dataset diverse,
        # or we can average the 12 months. Let's pick a random month for each point.
        
        logger.info("Reading raster values...")
        for i, (row, col) in enumerate(zip(rows, cols)):
            # Pick a random month (0-11) for this point
            month_idx = rng.integers(0, 12)
            
            # Read elevation
            with rasterio.open(elev_file) as src:
                elev = src.read(1, window=((row, row+1), (col, col+1)))[0,0]
            
            # Read temperature for selected month
            with rasterio.open(tavg_files[month_idx]) as src:
                temp = src.read(1, window=((row, row+1), (col, col+1)))[0,0]
            
            # Read precipitation for selected month
            with rasterio.open(prec_files[month_idx]) as src:
                prec = src.read(1, window=((row, row+1), (col, col+1)))[0,0]

            # Convert pixel to lat/lon
            lon, lat = xy(transform, col, row)

            # Handle nodata
            if np.isnan(temp) or np.isnan(prec) or np.isnan(elev):
                continue

            writer.writerow([lat, lon, temp, prec, elev, month_idx + 1])
            
            if (i + 1) % 10000 == 0:
                logger.info(f"Processed {i+1}/{sample_size} points")

    logger.info(f"Saved climate snapshots to {output_csv}")
    
    # Record checksum for output
    out_hash = calculate_sha256(output_csv)
    update_checksums_file(output_csv, out_hash, logger)
    update_artifact(STATE_FILE, output_csv.name, out_hash)

    return output_csv

def main():
    logger = setup_logging("fetch_worldclim")
    logger.info("Starting WorldClim data fetch...")
    
    result = fetch_worldclim_data(logger)
    
    if result is None:
        logger.error("WorldClim data fetch failed.")
        sys.exit(1)
    
    logger.info("WorldClim data fetch completed successfully.")

if __name__ == "__main__":
    main()
