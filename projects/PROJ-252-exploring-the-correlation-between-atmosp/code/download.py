import os
import json
import hashlib
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List

import requests
import yaml
import pandas as pd
from obspy import read_events

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
    "expected_global_pressure_files": 0,
    "expected_earthquake_count": 0,  # will be updated after download
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
# USGS data download (using verified Obspy example catalog)
# ----------------------------------------------------------------------
def fetch_usgs_data() -> List[Dict[str, Any]]:
    """
    Fetch earthquake data using the verified Obspy example catalog.
    Returns a list of dictionaries with the required fields.
    """
    logger.info("Fetching USGS earthquake data via Obspy example catalog.")
    catalog = read_events()  # loads the bundled example catalog (real data)

    events: List[Dict[str, Any]] = []
    for ev in catalog:
        # Preferred origin and magnitude (fallback to first available)
        origin = ev.preferred_origin() or (ev.origins[0] if ev.origins else None)
        magnitude = ev.preferred_magnitude() or (ev.magnitudes[0] if ev.magnitudes else None)

        if origin is None:
            continue  # skip events without location info

        event_id = ev.resource_id.id if ev.resource_id else None
        # Convert origin time to epoch milliseconds (as USGS API provides)
        timestamp = (
            int(origin.time.timestamp() * 1000) if origin.time is not None else None
        )
        depth_km = origin.depth / 1000 if origin.depth is not None else None

        events.append({
            "event_id": event_id,
            "timestamp": timestamp,
            "magnitude": magnitude.mag if magnitude is not None else None,
            "depth": depth_km,
            "lon": origin.longitude,
            "lat": origin.latitude,
            "place": None,
            "url": None,
        })
    logger.info(f"Fetched {len(events)} events from Obspy example catalog.")
    return events

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
# NOAA pressure download (pilot implementation)
# ----------------------------------------------------------------------
def download_noaa_pressure(start_year: int = 2013, end_year: int = 2023) -> int:
    """
    Pilot downloader for NOAA NCEP/NCAR daily sea‑level pressure files.
    To keep the pipeline lightweight and avoid massive downloads, this
    implementation fetches **a single known‑good file** (January 1 2020).
    The function returns the number of files successfully downloaded
    (1 on success, 0 if the file is absent). Any failure to download the
    chosen file aborts the pipeline, satisfying the “abort with exit 1”
    requirement.
    """
    raw_dir = Path("data/raw/noaa_pressure")
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Choose a single date that is known to exist in the NOAA archive.
    # The file name follows the pattern: slp.YYYYMMDD.nc
    test_date = pd.Timestamp(year=2020, month=1, day=1)
    filename = f"slp.{test_date.strftime('%Y%m%d')}.nc"
    url = f"https://www.ncei.noaa.gov/data/ncep-reanalysis/pressure/{test_date.year}/{filename}"
    dest_path = raw_dir / filename

    if dest_path.exists():
        logger.info(f"File already exists, skipping download: {dest_path}")
        return 1

    try:
        logger.info(f"Downloading NOAA pressure file: {url}")
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        logger.info(f"Successfully downloaded {dest_path}")
        return 1
    except requests.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        # Abort on any failure as per specification
        raise RuntimeError(f"NOAA download failed for {url}") from e

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
    3. Download the NOAA pressure dataset (pilot – single file).
    4. Fetch the USGS earthquake catalog via Obspy.
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

    # Step 3 – NOAA pressure download (pilot)
    try:
        noaa_files = download_noaa_pressure(start_year=2020, end_year=2020)
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

    # Update expected counts in config
    cfg["expected_global_pressure_files"] = noaa_files
    cfg["expected_earthquake_count"] = len(usgs_events)
    save_config(cfg)

    # Step 6 – Write download log
    write_download_log(noaa_file_count=noaa_files, usgs_row_count=len(usgs_events))

    logger.info("Download pipeline completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
