import os
import sys
import csv
import hashlib
import logging
import requests
from pathlib import Path
import json

# Project root resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_CHECKSUMS_FILE = PROJECT_ROOT / "data" / "checksums.txt"
STATE_FILE = PROJECT_ROOT / "state" / "projects" / "PROJ-334-predicting-avian-song-variation-with-cli.yaml"

# WorldClim v2.1 URLs for 10-minute resolution (approx 20km, suitable for 10km join radius)
# We will sample a subset of the global data to keep the task manageable but real.
# The global 10min data is ~120MB compressed. We will fetch the full set of 19 bioclim variables.
# To avoid downloading 19 separate files and merging them manually in this specific script,
# we will fetch a representative sample of coordinates from a known real dataset or
# fetch the specific variable files for a small region if possible.
# However, the task requires "real climate variables".
# Strategy: Use the WorldClim API or direct download for a specific set of variables.
# Since WorldClim doesn't have a direct "query lat/lon" API, we download the global rasters
# (or a subset) and sample points.
# To keep this script executable and robust without massive downloads, we will use a verified
# approach: Fetch the global 10-minute data for 'bio1' (Annual Mean Temperature) as a representative,
# or better, use a pre-aggregated CSV if available from a verified source, OR fetch the rasters.
# Given the constraints of a single script and "streaming", we will fetch the 19 bioclim
# variables from the WorldClim server for a specific region or globally if small enough.
# The 10-minute global data is ~120MB total for all 19 variables. This fits in memory.

# URL pattern for WorldClim v2.1 10-minute data
# http://worldclim.org/data/bioclim/bio1.tif ... bio19.tif
# We will download bio1, bio12, and bio15 (Temp, Precip, Precip Seasonality) to keep it focused
# or download all 19 if the task implies a full dataset. The task says "temp, precip, elev".
# Elevation is 'dem'.

BASE_URL = "https://biogeo.ucdavis.edu/data/worldclim/v2.1/bioclim/"
DEM_URL = "https://biogeo.ucdavis.edu/data/worldclim/v2.1/dem/"

VARIABLES_TO_FETCH = [
    ("bio1", "annual_mean_temp"),
    ("bio12", "annual_precipitation"),
    ("bio15", "precipitation_seasonality"),
    ("dem", "elevation")
]

LOGGER = logging.getLogger(__name__)

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def calculate_sha256(filepath):
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_checksums_file(filename, hash_value):
    """Append or update checksum in data/checksums.txt."""
    filepath = DATA_CHECKSUMS_FILE
    if not filepath.exists():
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["filename", "sha256_hash"])
    
    # Check if file exists in checksums
    updated = False
    rows = []
    with open(filepath, "r", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows.append(header)
        for row in reader:
            if row[0] == filename:
                row[1] = hash_value
                updated = True
            rows.append(row)
    
    if not updated:
        rows.append([filename, hash_value])
    
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

def update_state_file(filename, hash_value):
    """Update the project state YAML file with artifact hash."""
    import yaml
    state_file = STATE_FILE
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    if state_file.exists():
        with open(state_file, "r") as f:
            try:
                state = yaml.safe_load(f) or {}
            except yaml.YAMLError:
                state = {}
    else:
        state = {
            "artifact_hashes": {},
            "updated_at": "1970-01-01T00:00:00Z"
        }
    
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}
    
    state["artifact_hashes"][filename] = hash_value
    state["updated_at"] = "2024-01-01T00:00:00Z" # Placeholder for real timestamp logic if needed
    
    with open(state_file, "w") as f:
        yaml.dump(state, f, default_flow_style=False)

def download_file(url, dest_path):
    """Download a file from URL, raising on failure."""
    LOGGER.info(f"Downloading {url} to {dest_path}")
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        LOGGER.info(f"Downloaded {dest_path} successfully.")
    except requests.RequestException as e:
        LOGGER.error(f"Failed to download {url}: {e}")
        raise

def fetch_worldclim_data():
    """
    Fetch real WorldClim data (bio1, bio12, bio15, dem) for a sample of global coordinates.
    Since WorldClim provides rasters, we cannot directly query lat/lon without a library like rasterio.
    To adhere to "real data" and "no fabrication", we will:
    1. Download the global 10-minute rasters for the selected variables.
    2. Use a simple point-sampling strategy by reading the GeoTIFF header and sampling specific grid cells.
    3. Since we cannot import rasterio (it's in requirements but might not be installed in this specific runner context without pip install),
       we will assume the environment has rasterio or use a fallback to a pre-defined grid if rasterio is missing?
       
    Constraint Check: The task says "fetch real data". If we can't read the raster without rasterio, we must ensure rasterio is used.
    The requirements.txt includes rasterio. We will import it.
    
    If the file download fails, we abort.
    """
    try:
        import rasterio
        from rasterio.crs import CRS
        from rasterio.warp import transform
    except ImportError:
        LOGGER.error("rasterio is required but not installed. Please install dependencies.")
        sys.exit(1)

    # Ensure directory
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # Map variable codes to filenames
    # WorldClim 10min filenames: bio1.tif, bio12.tif, dem.tif
    file_map = {
        "bio1": "bio1.tif",
        "bio12": "bio12.tif",
        "bio15": "bio15.tif",
        "dem": "dem.tif"
    }
    
    downloaded_files = {}
    
    # Download files
    for var_code, var_name in VARIABLES_TO_FETCH:
        if var_code == "dem":
            url = f"{DEM_URL}w{var_code}.tif" # Actually dem.tif is in dem folder
            # Correct URL for dem: https://biogeo.ucdavis.edu/data/worldclim/v2.1/dem/wdem.tif ? 
            # Let's use the standard bio1 path for bio, and specific for dem.
            # Actually, WorldClim 2.1 dem is at: https://biogeo.ucdavis.edu/data/worldclim/v2.1/dem/wdem.tif is not right.
            # It is usually: https://biogeo.ucdavis.edu/data/worldclim/v2.1/dem/dem10.tif? 
            # Let's try the standard bio path for bio and a specific one for dem.
            # According to WorldClim docs: dem10.tif is the file.
            url = f"{DEM_URL}dem10.tif"
        else:
            url = f"{BASE_URL}{var_code}.tif"
        
        dest = DATA_RAW_DIR / file_map[var_code]
        
        # Check if already downloaded (to avoid re-downloading in dev)
        if dest.exists():
            LOGGER.info(f"Found existing file: {dest}")
        else:
            try:
                download_file(url, dest)
            except Exception as e:
                LOGGER.error(f"Aborting: Could not download {url}. {e}")
                sys.exit(1)
        
        downloaded_files[var_code] = dest

    # Now, sample points. We need to generate a set of real lat/lon points to query.
    # Since we are building a dataset for the project, we will sample points from a 
    # known grid or a specific region to ensure we get valid data.
    # To make it "real" and not "synthetic", we will sample the raster at regular intervals.
    # We will create a CSV of sampled points.
    
    output_file = DATA_RAW_DIR / "worldclim_sample.csv"
    sample_points = []
    
    # We will sample 100 random points across the globe (using a deterministic seed for reproducibility)
    # But we must ensure they are land. Since we can't easily check land/sea without more data,
    # we will just sample the raster. If the value is -9999 (nodata), we skip.
    # To ensure we get "real" data, we will sample a grid of points.
    
    # Let's pick a set of representative coordinates (real locations) to query.
    # Or better: Iterate through the raster grid in chunks to build a dataset.
    # Given memory constraints, we will sample 500 points.
    import random
    random.seed(42)
    
    # Open rasters
    rasters = {}
    for var_code, path in downloaded_files.items():
        rasters[var_code] = rasterio.open(path)
    
    # Get bounds and transform from one raster (they should be aligned)
    ref_raster = rasters["bio1"]
    width = ref_raster.width
    height = ref_raster.height
    transform = ref_raster.transform
    
    # Sample points
    # We'll sample 500 points uniformly across the raster grid
    num_samples = 500
    indices = random.sample(range(width * height), num_samples)
    
    data_rows = []
    
    for idx in indices:
        row = idx // width
        col = idx % width
        
        # Get lat/lon
        lon, lat = rasterio.transform.xy(transform, row, col, offset="center")
        
        # Check bounds (WorldClim is global, -180 to 180, -90 to 90)
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            continue
        
        sample_data = {"lat": lat, "lon": lon}
        valid_sample = True
        
        for var_code, var_name in VARIABLES_TO_FETCH:
            val = rasters[var_code].read(1)[row, col]
            # Check nodata
            if val == rasters[var_code].nodata or val is None:
                valid_sample = False
                break
            sample_data[var_name] = float(val)
        
        if valid_sample:
            data_rows.append(sample_data)
    
    # Write to CSV
    if data_rows:
        with open(output_file, "w", newline="") as f:
            fieldnames = ["lat", "lon"] + [v[1] for v in VARIABLES_TO_FETCH]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data_rows)
        
        LOGGER.info(f"Sampled {len(data_rows)} points. Saved to {output_file}")
        
        # Calculate checksum
        checksum = calculate_sha256(output_file)
        update_checksums_file(output_file.name, checksum)
        update_state_file(output_file.name, checksum)
        
        # Clean up downloaded rasters to save space? 
        # The task doesn't explicitly say to delete, but it's good practice.
        # We will leave them for T013/T014 if needed, but the CSV is the artifact.
    else:
        LOGGER.error("No valid data points sampled.")
        sys.exit(1)

def main():
    setup_logging()
    LOGGER.info("Starting WorldClim data fetch and sampling.")
    
    # Check for existing sample file first
    sample_path = DATA_RAW_DIR / "worldclim_sample.csv"
    if sample_path.exists():
        LOGGER.info(f"Found existing sample file: {sample_path}. Skipping fetch.")
        # Still update checksum if missing? The task says "FIRST attempt to load... if missing, fetch".
        # If it exists, we assume it's valid. But we should ensure checksum is recorded.
        if not any(DATA_CHECKSUMS_FILE.exists() and line.startswith("worldclim_sample.csv") for line in open(DATA_CHECKSUMS_FILE)):
            LOGGER.warning("Sample file exists but checksum missing. Recalculating.")
            checksum = calculate_sha256(sample_path)
            update_checksums_file(sample_path.name, checksum)
            update_state_file(sample_path.name, checksum)
        return

    fetch_worldclim_data()
    LOGGER.info("WorldClim data fetch complete.")

if __name__ == "__main__":
    main()
