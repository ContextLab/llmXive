import sys
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import yaml
import pandas as pd
import netCDF4  # used to read the NetCDF file for record count
import xarray as xr
from obspy import UTCDateTime
from obspy.clients.fdsn import Client

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Paths (relative to project root)
CONFIG_PATH = Path("data/processed/config.yaml")
RAW_PRESSURE_PATH = Path("data/raw/pressure.nc")
RAW_USGS_PATH = Path("data/raw/usgs_2013_2023.csv")
LOG_PATH = Path("logs/download_success.log")

# Default configuration (used if config.yaml does not exist)
DEFAULT_CONFIG = {
    "pilot_mode": False,
    "expected_global_pressure_files": 1,
    "expected_earthquake_count": 0,
    "pressure_sha256": "",
    "usgs_sha256": "",
    "pressure_record_count": 0,
    "moving_average_days": 30,
    "min_permutation_iterations": 1000,
    "max_permutation_iterations": 10000,
    "convergence_variance_threshold": 1e-5
}

def get_robust_session() -> requests.Session:
    """Create a requests session with retries and a common browser User‑Agent."""
    session = requests.Session()
    retry_strategy = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
    })
    return session

def load_config() -> Dict[str, Any]:
    """Load existing config or create a default one."""
    if not CONFIG_PATH.exists():
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.safe_dump(DEFAULT_CONFIG, f)
        return DEFAULT_CONFIG.copy()
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_config(cfg: Dict[str, Any]) -> None:
    """Write the configuration back to disk."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f)

def _sha256_of_file(path: Path) -> str:
    """Calculate the SHA‑256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            sha256.update(block)
    return sha256.hexdigest()

def _count_pressure_records(path: Path) -> int:
    """
    Return the number of time records in the NetCDF pressure file.
    Uses netCDF4 directly to avoid heavy xarray import overhead.
    """
    try:
        with netCDF4.Dataset(str(path), mode="r") as ds:
            if "time" in ds.dimensions:
                return int(ds.dimensions["time"].size)
            else:
                raise RuntimeError("NetCDF file has no 'time' dimension.")
    except Exception as e:
        logger.error(f"Failed to read pressure NetCDF file for record count: {e}")
        raise

def download_noaa_pressure() -> None:
    """
    Stream the NOAA NCEP/NCAR sea‑level pressure dataset via OPeNDAP and write it
    locally as a NetCDF file.
    """
    RAW_PRESSURE_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Verified OPeNDAP URL for the full daily mean sea‑level pressure reanalysis
    url = (
        "https://psl.noaa.gov/thredds/dodsC/Datasets/ncep.reanalysis.dailyavgs/pressure/mslp.daily.nc"
    )
    logger.info(f"Downloading NOAA pressure dataset from {url}")

    try:
        # Open remote dataset lazily with dask chunks
        ds = xr.open_dataset(url, chunks={"time": 30})
        # Write to local NetCDF – this will stream the data chunk‑by‑chunk
        ds.to_netcdf(RAW_PRESSURE_PATH, compute=True)
    except Exception as e:
        logger.error(f"Failed to download NOAA pressure dataset: {e}")
        raise RuntimeError(f"Critical failure downloading NOAA dataset: {e}")

    logger.info(f"Pressure dataset saved to {RAW_PRESSURE_PATH}")

def fetch_usgs_data() -> int:
    """
    Retrieve the USGS earthquake catalog (M ≥ 4.0, depth ≤ 70 km) for 2013‑2023
    using the verified ObsPy client. Writes CSV to RAW_USGS_PATH and returns
    the number of rows written.
    """
    RAW_USGS_PATH.parent.mkdir(parents=True, exist_ok=True)

    client = Client("USGS")
    starttime = UTCDateTime("2013-01-01")
    endtime = UTCDateTime("2023-12-31")
    logger.info(
        f"Fetching USGS earthquake catalog from {starttime.isoformat()} to {endtime.isoformat()}"
    )

    try:
        cat = client.get_events(
            starttime=starttime,
            endtime=endtime,
            minmagnitude=4.0,
            maxdepth=70,
            includearrivals=False,
            limit=None,
        )
    except Exception as e:
        logger.error(f"Failed to fetch USGS data via ObsPy: {e}")
        raise RuntimeError(f"Critical failure fetching USGS data: {e}")

    records = []
    for ev in cat:
        # Extract primary origin
        origin = ev.preferred_origin() or ev.origins[0]
        magnitude = ev.preferred_magnitude() or ev.magnitudes[0]
        event_id = ev.resource_id.id.split("/")[-1]  # e.g., "us7000abcd"
        records.append({
            "event_id": event_id,
            "timestamp": origin.time.strftime("%Y-%m-%dT%H:%M:%S"),
            "latitude": origin.latitude,
            "longitude": origin.longitude,
            "magnitude": magnitude.mag,
            "depth": origin.depth / 1000.0,  # convert meters to km
        })

    df = pd.DataFrame(records)
    df.to_csv(RAW_USGS_PATH, index=False)
    logger.info(f"USGS catalog download complete, rows: {len(df)}")
    return len(df)

def main() -> int:
    """
    Entry point for T002. Downloads both datasets (if missing or checksum‑mismatched),
    validates them, writes a log, and updates config.yaml.
    Returns 0 on success, 1 on failure.
    """
    logger.info("Starting T002: Data Acquisition Pipeline.")
    try:
        cfg = load_config()
        needs_download = False

        # Determine whether we need to (re)download
        if not (RAW_PRESSURE_PATH.exists() and RAW_USGS_PATH.exists()):
            logger.info("One or both raw files are missing – initiating download.")
            needs_download = True
        else:
            # Verify checksums against stored values
            pressure_sha = _sha256_of_file(RAW_PRESSURE_PATH)
            usgs_sha = _sha256_of_file(RAW_USGS_PATH)
            if (pressure_sha != cfg.get("pressure_sha256") or
                    usgs_sha != cfg.get("usgs_sha256")):
                logger.info("Checksum mismatch detected – re‑downloading.")
                needs_download = True
            else:
                logger.info("Existing files match recorded checksums – no download needed.")

        if needs_download:
            # Download pressure data
            download_noaa_pressure()

            # Download USGS catalog
            usgs_row_count = fetch_usgs_data()

            # Compute pressure record count
            pressure_record_count = _count_pressure_records(RAW_PRESSURE_PATH)
            logger.info(f"Pressure dataset contains {pressure_record_count} time records.")

            # Update configuration with new metadata
            cfg.update({
                "pilot_mode": False,
                "expected_global_pressure_files": 1,
                "expected_earthquake_count": usgs_row_count,
                "pressure_sha256": _sha256_of_file(RAW_PRESSURE_PATH),
                "usgs_sha256": _sha256_of_file(RAW_USGS_PATH),
                "pressure_record_count": pressure_record_count,
                "moving_average_days": 30
            })
            save_config(cfg)
        else:
            # Use existing metadata from config (already validated)
            pressure_record_count = cfg.get("pressure_record_count", 0)
            usgs_row_count = cfg.get("expected_earthquake_count", 0)

        # Final sanity checks
        if not (RAW_PRESSURE_PATH.exists() and RAW_USGS_PATH.exists()):
            raise FileNotFoundError("Required raw data files are missing after download step.")

        final_pressure_count = _count_pressure_records(RAW_PRESSURE_PATH)
        if final_pressure_count <= 0:
            raise ValueError("Pressure dataset contains no time records.")

        # Verify USGS row count tolerance (±1 % of expected if we have an expectation)
        df_usgs = pd.read_csv(RAW_USGS_PATH)
        actual_usgs_count = len(df_usgs)
        expected_usgs = cfg.get("expected_earthquake_count", 0)
        if expected_usgs > 0:
            diff = abs(actual_usgs_count - expected_usgs)
            if diff > (0.01 * expected_usgs):
                raise ValueError(
                    f"USGS row count out of tolerance: expected {expected_usgs}, got {actual_usgs_count}"
                )

        # Write success log
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "w", encoding="utf-8") as log_f:
            log_f.write(f"Pressure data downloaded: {final_pressure_count} days\\n")
            log_f.write(f"USGS catalog rows: {actual_usgs_count}\\n")

        logger.info(
            f"T002 completed successfully – pressure records: {final_pressure_count}, "
            f"USGS rows: {actual_usgs_count}"
        )
        return 0
    except Exception as e:
        logger.critical(f"T002 failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
