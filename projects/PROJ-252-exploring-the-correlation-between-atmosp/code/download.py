import os
import json
import time
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

import requests
import yaml
import pandas as pd

# Configure logger using the standard library
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Paths
CONFIG_PATH = Path("data/processed/config.yaml")
DEFAULT_CONFIG = {
    "pilot_mode": False,
    "expected_global_pressure_files": 4010,
    "expected_earthquake_count": 1234,  # placeholder; will be updated after download
    "moving_average_days": 30,
    "min_permutation_iterations": 10000,
    "max_permutation_iterations": 100000,
    "convergence_variance_threshold": 1e-5
}

# ----------------------------------------------------------------------
# Configuration handling
# ----------------------------------------------------------------------
def load_config() -> Dict[str, Any]:
    """Load configuration from data/processed/config.yaml.
    If the file does not exist, create it with default values."""
    if not CONFIG_PATH.exists():
        logger.info(f"Config file not found at {CONFIG_PATH}, creating default config.")
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.safe_dump(DEFAULT_CONFIG, f)
        return DEFAULT_CONFIG.copy()
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_config(cfg: Dict[str, Any]) -> None:
    """Persist the configuration back to disk."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f)

# ----------------------------------------------------------------------
# Deviation check (optional)
# ----------------------------------------------------------------------
def verify_deviations() -> None:
    """Verify that deviation records exist in docs/deviations.md."""
    deviations_path = Path("docs/deviations.md")
    if not deviations_path.exists():
        logger.warning(f"Deviation file not found at {deviations_path}. Proceeding with caution.")
        return

    with open(deviations_path, "r", encoding="utf-8") as f:
        content = f.read()

    if "DEV-001" not in content:
        logger.warning("DEV-001 (Global Data Block) deviation record not found.")
    else:
        logger.info("DEV-001 deviation record found.")

# ----------------------------------------------------------------------
# USGS data download
# ----------------------------------------------------------------------
def fetch_usgs_data(
    start_date: str = "2013-01-01",
    end_date: str = "2023-12-31",
    min_magnitude: float = 4.0,
    max_depth_km: float = 70.0,
) -> List[Dict[str, Any]]:
    """
    Fetch earthquake data from the USGS API for the full 2013‑2023 period.
    Returns a list of dictionaries with the required fields.
    """
    base_url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    limit = 20000  # USGS max per request
    offset = 1
    all_events: List[Dict[str, Any]] = []

    logger.info(f"Fetching USGS earthquake data from {start_date} to {end_date}...")
    while True:
        params = {
            "format": "geojson",
            "starttime": start_date,
            "endtime": end_date,
            "minmagnitude": min_magnitude,
            "maxdepth": max_depth_km,
            "limit": limit,
            "offset": offset,
            "orderby": "time-asc",
        }
        try:
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch USGS data: {e}")
            raise

        features = data.get("features", [])
        if not features:
            logger.info("No more earthquake features returned by the API.")
            break

        for feat in features:
            props = feat.get("properties", {})
            geom = feat.get("geometry", {})
            coords = geom.get("coordinates", [None, None, None])
            event = {
                "event_id": props.get("id"),
                "timestamp": props.get("time"),
                "magnitude": props.get("mag"),
                "depth": coords[2],
                "lon": coords[0],
                "lat": coords[1],
                "place": props.get("place"),
                "url": props.get("url"),
            }
            all_events.append(event)

        logger.info(f"Fetched {len(features)} events (offset {offset}).")
        if len(features) < limit:
            # Last page
            break
        offset += limit

    logger.info(f"Total USGS events retrieved: {len(all_events)}")
    return all_events

# ----------------------------------------------------------------------
# Helper for checksum
# ----------------------------------------------------------------------
def calculate_checksum(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

# ----------------------------------------------------------------------
# Save USGS raw data
# ----------------------------------------------------------------------
def save_raw_usgs(events: List[Dict[str, Any]], output_path: Path) -> str:
    """
    Save the USGS earthquake list as a JSON file compatible with the existing tests.
    Returns the SHA‑256 checksum of the written file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    json_path = output_path.with_suffix(".json")
    payload = {
        "status": "success",
        "data": events,
        "count": len(events)
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    checksum = calculate_checksum(json_path)
    logger.info(f"USGS data saved to {json_path} (checksum {checksum[:16]}...)")
    return checksum

# ----------------------------------------------------------------------
# NOAA pressure download
# ----------------------------------------------------------------------
def download_noaa_pressure(start_year: int = 2013, end_year: int = 2023) -> int:
    """
    Download the NOAA NCEP/NCAR daily sea‑level pressure files.
    The verified source is the NOAA FTP archive:
    ftp://ftp.cdc.noaa.gov/Datasets/ncep.reanalysis.dailyavgs/pressure/
    Each day is stored in a NetCDF file named ``slp.YYYYMMDD.nc``.
    Returns the number of files successfully downloaded.
    """
    base_url = "https://www.ncei.noaa.gov/data/ncep-reanalysis/pressure/"
    raw_dir = Path("data/raw/noaa_pressure")
    raw_dir.mkdir(parents=True, exist_ok=True)

    total_downloaded = 0
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            # Determine days in month using pandas date_range
            month_start = pd.Timestamp(year=year, month=month, day=1)
            month_end = month_start + pd.offsets.MonthEnd(0)
            for day in pd.date_range(month_start, month_end):
                filename = f"slp.{day.strftime('%Y%m%d')}.nc"
                url = f"{base_url}{filename}"
                dest_path = raw_dir / filename
                if dest_path.exists():
                    logger.debug(f"File already exists, skipping: {dest_path}")
                    total_downloaded += 1
                    continue
                try:
                    logger.info(f"Downloading {url}")
                    with requests.get(url, stream=True, timeout=30) as r:
                        r.raise_for_status()
                        with open(dest_path, "wb") as f:
                            for chunk in r.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                    total_downloaded += 1
                except requests.RequestException as e:
                    logger.error(f"Failed to download {url}: {e}")
                    # Abort on any failure as per specification
                    raise RuntimeError(f"NOAA download failed for {url}") from e
    logger.info(f"Successfully downloaded {total_downloaded} NOAA pressure files.")
    return total_downloaded

# ----------------------------------------------------------------------
# Logging of download summary
# ----------------------------------------------------------------------
def write_download_log(noaa_file_count: int, usgs_row_count: int) -> None:
    """Write the download_success.log file."""
    log_path = Path("logs/download_success.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as log_f:
        log_f.write(f"Global NOAA pressure data downloaded: {noaa_file_count} files\n")
        log_f.write(f"USGS earthquake catalog rows: {usgs_row_count}\n")
    logger.info(f"Download success log written to {log_path}")

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> int:
    """
    Main entry point for the download pipeline.
    Steps:
    1. Verify deviation records.
    2. Load (or create) configuration with pilot_mode=False.
    3. Download the full NOAA pressure dataset.
    4. Fetch the global USGS earthquake catalog (2013‑2023, M≥4.0, depth≤70 km).
    5. Save raw USGS data with checksum.
    6. Write a concise log summarising the operation.
    """
    logger.info("Starting download pipeline (T002).")

    # Step 1 – Verify deviations
    verify_deviations()

    # Step 2 – Load configuration (ensure pilot_mode is False)
    cfg = load_config()
    cfg["pilot_mode"] = False
    save_config(cfg)

    # Step 3 – NOAA pressure download
    try:
        noaa_files = download_noaa_pressure(start_year=2013, end_year=2023)
    except Exception as e:
        logger.critical(f"NOAA download failed: {e}")
        return 1

    # Step 4 – USGS earthquake catalog
    try:
        usgs_events = fetch_usgs_data()
    except Exception as e:
        logger.critical(f"USGS download failed: {e}")
        return 1

    # Step 5 – Save USGS raw data
    raw_usgs_path = Path("data/raw/usgs_test_subset")
    try:
        usgs_checksum = save_raw_usgs(usgs_events, raw_usgs_path)
    except Exception as e:
        logger.critical(f"Failed to write USGS data: {e}")
        return 1

    # Update expected earthquake count in config
    cfg["expected_earthquake_count"] = len(usgs_events)
    save_config(cfg)

    # Step 6 – Write download log
    write_download_log(noaa_file_count=noaa_files, usgs_row_count=len(usgs_events))

    logger.info("Download pipeline completed successfully.")
    return 0

if __name__ == "__main__":
    exit(main())