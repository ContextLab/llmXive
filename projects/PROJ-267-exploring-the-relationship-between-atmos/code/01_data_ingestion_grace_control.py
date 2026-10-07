import os
import sys
import logging
import hashlib
import json
import time
from pathlib import Path
import requests
import pandas as pd
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "urls.yaml"
OUTPUT_DIR = PROJECT_ROOT / "data" / "raw" / "grace-fo" / "control"

def load_config():
    """Load the verified URLs from config/urls.yaml."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}. Run T007c/d/e first.")
    
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
    
    # Verify the specific key exists
    if 'grace_fo_mascon_csr_rl06' not in config.get('urls', {}):
        raise KeyError("Missing 'grace_fo_mascon_csr_rl06' in config/urls.yaml. Run T007c.")
    
    return config

def calculate_sha256(file_path):
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_grace_data(url, output_path, timeout=300):
    """
    Fetch GRACE-FO data from the provided URL.
    Raises an error if the fetch fails (no synthetic fallback).
    """
    logger.info(f"Fetching data from: {url}")
    logger.info(f"Saving to: {output_path}")
    
    try:
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        
        # Write file in chunks
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        logger.info("Download completed successfully.")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch data: {e}")
        raise RuntimeError(f"Real data fetch failed: {e}")

def filter_region(df, region_type='control'):
    """
    Filter the GRACE-FO mascon data to the specified region.
    
    Control Region (East Coast NA):
    - Latitude: 25°N to 55°N
    - Longitude: 75°W to 105°W (approx -105 to -75)
    
    Target Region (West Coast NA) would be:
    - Latitude: 30°N to 50°N
    - Longitude: 125°W to 155°W (approx -155 to -125)
    
    This function filters for the CONTROL region as per T015b.
    """
    logger.info(f"Filtering data for {region_type} region...")
    
    # Define bounding box for Control Region (East Coast NA)
    # Note: Longitudes are typically negative in Western Hemisphere
    min_lat, max_lat = 25.0, 55.0
    min_lon, max_lon = -105.0, -75.0  # 75W to 105W
    
    # Check if necessary columns exist
    required_cols = ['lat', 'lon', 'value'] # Assuming standard mascon columns
    if not all(col in df.columns for col in required_cols):
        # Try to infer or log warning if columns differ, but proceed with standard assumption
        logger.warning(f"Standard columns {required_cols} not found. Checking for alternatives...")
        # Fallback if column names differ slightly (common in mascon datasets)
        if 'latitude' in df.columns:
            df = df.rename(columns={'latitude': 'lat', 'longitude': 'lon'})
        else:
            raise ValueError(f"Could not identify latitude/longitude columns in dataframe. Columns: {df.columns}")

    # Apply filtering
    filtered_df = df[
        (df['lat'] >= min_lat) & 
        (df['lat'] <= max_lat) & 
        (df['lon'] >= min_lon) & 
        (df['lon'] <= max_lon)
    ].copy()
    
    logger.info(f"Filtered data shape: {filtered_df.shape}")
    logger.info(f"Original data shape: {df.shape}")
    
    if filtered_df.empty:
        logger.warning("No data found in the specified control region. This might be expected if the dataset is sparse or the bounding box needs adjustment.")
    
    return filtered_df

def save_raw_data(df, output_dir, file_name):
    """Save the filtered dataframe to a CSV and record the checksum."""
    output_path = output_dir / file_name
    
    # Ensure directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Saved filtered data to: {output_path}")
    
    # Calculate and save checksum
    checksum = calculate_sha256(output_path)
    checksum_file = output_dir / f"{file_name}.sha256"
    with open(checksum_file, 'w') as f:
        f.write(f"{checksum}  {file_name}\n")
    
    logger.info(f"Saved checksum to: {checksum_file} (SHA-256: {checksum})")
    return output_path, checksum

def log_dataset_version(df, output_dir):
    """Log dataset version/release date if available in metadata or file name."""
    # Attempt to extract version from the source file or df metadata
    # Since we are fetching raw files, we might not have explicit version in the CSV unless it's in the header
    # For now, log the count and date range
    if 'date' in df.columns:
        date_range = f"{df['date'].min()} to {df['date'].max()}"
    else:
        date_range = "N/A"
    
    log_entry = {
        "region": "control",
        "records": len(df),
        "date_range": date_range,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    log_file = output_dir / "dataset_info.json"
    with open(log_file, 'w') as f:
        json.dump(log_entry, f, indent=2)
    
    logger.info(f"Logged dataset info to: {log_file}")
    return log_entry

def main():
    """Main execution flow for T015b."""
    logger.info("=== GRACE-FO Control Region Data Ingestion Start ===")
    
    # 1. Load Config
    config = load_config()
    base_url = config['urls']['grace_fo_mascon_csr_rl06']
    
    # 2. Determine file to fetch
    # The URL in config/urls.yaml is the base or specific file. 
    # Based on T015 failure, the specific file path might need to be constructed or is a directory listing.
    # However, T007c populated the URL. We assume it points to the latest or a specific file.
    # If the URL is a directory, we might need to parse it, but standard practice is a direct file link.
    # Let's assume the URL in config is the direct link to the latest CSR RL06 Mascon file.
    # If the URL ends in a directory, we might need to handle that, but for now, we treat it as a file.
    
    # Note: The previous failure showed a 404 on a specific file. 
    # T007c should have fixed the URL. We trust the config now.
    # We will try to fetch the file. If it's a directory listing, requests.get might fail or return HTML.
    # We assume the config contains a direct file link as per T007c requirements.
    
    # To be robust, if the URL doesn't end in .nc or .csv, we might need to adjust, 
    # but the task says "reads the verified URL".
    
    output_filename = "grace-fo-control-raw.csv"
    output_path = OUTPUT_DIR / output_filename
    
    # 3. Fetch Data
    # We need to handle the fact that GRACE-FO data is often NetCDF.
    # We will fetch it, then convert to CSV for downstream processing if necessary.
    # However, the task says "saves raw files". If the source is NetCDF, we save NetCDF.
    # But downstream (T017a) expects CSVs. 
    # Let's assume the URL points to a CSV or we convert it.
    # Given the previous failure was 404 on a .nc file, let's assume the config URL is now correct.
    # If the config URL points to a .nc, we download .nc.
    # If it points to a CSV, we download CSV.
    
    # Let's check the extension of the URL to determine output format
    if base_url.endswith('.nc'):
        raw_filename = "grace-fo-control-raw.nc"
    else:
        raw_filename = "grace-fo-control-raw.csv"
    
    # We will download the file as is, then process if needed.
    # But the task requires saving "raw files" and recording checksums.
    # Let's download the file first.
    
    try:
        # If the URL is a directory, we might need to list files. 
        # But T007c implies a specific URL was verified.
        # We will attempt to fetch the resource at the URL.
        response = requests.head(base_url, timeout=10)
        if response.status_code == 200:
            # It's a file
            logger.info("URL points to a file.")
            fetch_grace_data(base_url, OUTPUT_DIR / raw_filename)
        else:
            # It might be a directory or error. 
            # If it's a directory, we can't fetch a single file without parsing.
            # We assume T007c provided a direct file URL.
            raise RuntimeError(f"URL does not point to a valid file (HEAD status: {response.status_code}). Check config/urls.yaml.")
    except Exception as e:
        logger.error(f"Error checking URL: {e}")
        raise

    # 4. Load and Filter (if NetCDF, use netCDF4 or xarray; if CSV, use pandas)
    # For robustness, we assume the downloaded file might be NetCDF (common for GRACE).
    # We need to convert to CSV for T017a.
    # However, T015b says "saves raw files". T017a says "loads downloaded mascon CSVs".
    # This implies T015b should produce CSVs if T017a expects CSVs.
    # Let's assume the downloaded file is NetCDF and we convert it to CSV here.
    
    import netCDF4 as nc # Optional dependency, might not be installed.
    # If netCDF4 is not installed, we might need to handle the case where it's already CSV.
    # Let's try to detect and convert.
    
    raw_file_path = OUTPUT_DIR / raw_filename
    
    if raw_file_path.suffix == '.nc':
        logger.info("Converting NetCDF to CSV for downstream compatibility...")
        try:
            ds = nc.Dataset(raw_file_path, 'r')
            # Extract variables. Standard GRACE-FO Mascon variables:
            # lat, lon, time, latitude, longitude, time, data (mascon values)
            # We need to map these to 'lat', 'lon', 'value', 'date'
            
            lats = ds.variables['lat'][:] if 'lat' in ds.variables else ds.variables['latitude'][:]
            lons = ds.variables['lon'][:] if 'lon' in ds.variables else ds.variables['longitude'][:]
            values = ds.variables['data'][:] # or 'mascon', 'rl06' etc.
            
            # Flatten arrays if necessary
            if len(lats.shape) > 1:
                lats, lons = np.meshgrid(lats, lons)
                lats = lats.flatten()
                lons = lons.flatten()
                values = values.flatten()
            
            # Create DataFrame
            df = pd.DataFrame({
                'lat': lats,
                'lon': lons,
                'value': values
            })
            
            # If time is available, add date column
            if 'time' in ds.variables:
                times = ds.variables['time'][:]
                # Convert to date string (simplified)
                # GRACE-FO time is usually days since 1970-01-01
                import numpy as np
                dates = pd.to_datetime(times, unit='D', origin='1970-01-01').strftime('%Y-%m-%d')
                # If multiple times, we might need to repeat or select one.
                # For simplicity, if multiple times, we take the last or average?
                # Mascon solutions are usually monthly.
                # We'll assume the file contains one month's data or we need to iterate.
                # For T015b, we just fetch and save.
                # We'll add a 'date' column if possible.
                if len(dates) == len(df):
                    df['date'] = dates
                elif len(dates) == 1:
                    df['date'] = dates[0]
            
            ds.close()
            
            # Save as CSV
            csv_path = OUTPUT_DIR / "grace-fo-control-raw.csv"
            df.to_csv(csv_path, index=False)
            logger.info(f"Converted and saved CSV to: {csv_path}")
            
            # Update raw_filename to CSV for checksum
            raw_filename = "grace-fo-control-raw.csv"
            raw_file_path = csv_path
            
        except Exception as e:
            logger.error(f"Failed to convert NetCDF to CSV: {e}")
            # If conversion fails, we can't proceed with CSV-based downstream.
            # We raise an error.
            raise RuntimeError("Failed to convert NetCDF to CSV. Downstream scripts expect CSV.")
    else:
        # Assume it's already CSV
        logger.info("Assuming downloaded file is CSV.")
        # Verify it loads
        try:
            df = pd.read_csv(raw_file_path)
        except Exception as e:
            raise RuntimeError(f"Failed to read downloaded file as CSV: {e}")

    # 5. Filter Region
    filtered_df = filter_region(df, region_type='control')

    # 6. Log Dataset Version
    log_dataset_version(filtered_df, OUTPUT_DIR)

    # 7. Save Raw Filtered Data (and checksum)
    # The task says "saves raw files". We have the raw CSV (filtered).
    # We save the filtered raw data.
    final_output_path, checksum = save_raw_data(filtered_df, OUTPUT_DIR, raw_filename)

    logger.info("=== GRACE-FO Control Region Data Ingestion Complete ===")

if __name__ == "__main__":
    main()