import os
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
import xarray as xr

# Attempt to import huggingface_hub for reliable file download
try:
    from huggingface_hub import hf_hub_download
except ImportError:
    hf_hub_download = None

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Paths
CONFIG_PATH = Path("data/processed/config.yaml")
RAW_PRESSURE_PATH = Path("data/raw/pressure.nc")
RAW_USGS_PATH = Path("data/raw/usgs_2013_2023.csv")
LOG_PATH = Path("logs/download_success.log")

# Default configuration
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
    """Create a requests session with retries and browser-like headers."""
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

    # Use a common browser User-Agent to prevent being blocked
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
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

def download_noaa_pressure() -> None:
    """Download the full NOAA NCEP/NCAR sea‑level pressure dataset."""
    RAW_PRESSURE_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Preferred method: huggingface_hub (handles redirects and auth)
    if hf_hub_download is not None:
        try:
            logger.info("Downloading NOAA pressure dataset via huggingface_hub.")
            downloaded_path = hf_hub_download(
                repo_id="noaa/ncep-reanalysis-pressures",
                filename="mslp_daily.nc",
                repo_type="dataset"
            )
            # Move the downloaded file to the expected location
            Path(downloaded_path).rename(RAW_PRESSURE_PATH)
            logger.info("Pressure dataset download complete via huggingface_hub.")
            return
        except Exception as e:
            logger.warning(f"huggingface_hub download failed: {e}")

    # Fallback: direct HTTP GET (may require authentication)
    url = "https://huggingface.co/datasets/noaa/ncep-reanalysis-pressures/resolve/main/mslp_daily.nc"
    session = get_robust_session()
    try:
        logger.info(f"Downloading NOAA pressure dataset from {url}")
        with session.get(url, stream=True, timeout=180) as r:
            r.raise_for_status()
            with open(RAW_PRESSURE_PATH, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
        logger.info("Pressure dataset download complete via direct HTTP.")
    except Exception as e:
        logger.error(f"Failed to download NOAA pressure data: {e}")
        raise RuntimeError(f"Critical failure downloading NOAA data: {e}")

def fetch_usgs_data() -> int:
    """Retrieve the USGS earthquake catalog (M >= 4.0, depth <= 70 km) for 2013-2023."""
    RAW_USGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    base_url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "csv",
        "starttime": "2013-01-01",
        "endtime": "2023-12-31",
        "minmagnitude": "4",
        "maxdepth": "70"
    }
    session = get_robust_session()
    try:
        logger.info(f"Fetching USGS earthquake catalog from {base_url}")
        with session.get(base_url, params=params, stream=True, timeout=180) as r:
            r.raise_for_status()
            with open(RAW_USGS_PATH, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)

        # Verify the CSV is valid and count rows
        df = pd.read_csv(RAW_USGS_PATH)
        logger.info(f"USGS catalog download complete, rows: {len(df)}")
        return len(df)
    except Exception as e:
        logger.error(f"Failed to fetch USGS data: {e}")
        raise RuntimeError(f"Critical failure fetching USGS data: {e}")

def _count_pressure_records() -> int:
    """Open the downloaded NetCDF file and return the number of time records."""
    try:
        with xr.open_dataset(RAW_PRESSURE_PATH, engine="netcdf4") as ds:
            count = int(ds.sizes.get("time", 0))
        return count
    except Exception as e:
        logger.error(f"Error reading NetCDF for record count: {e}")
        raise RuntimeError(f"Could not read NetCDF time dimension: {e}")

def main() -> int:
    logger.info("Starting T002: Data Acquisition Pipeline.")
    try:
        # Load or create configuration
        cfg = load_config()
        needs_download = False

        # Determine whether we need to (re)download
        if not (RAW_PRESSURE_PATH.exists() and RAW_USGS_PATH.exists()):
            logger.info("Missing raw files. Starting download.")
            needs_download = True
        else:
            p_sha = _sha256_of_file(RAW_PRESSURE_PATH)
            u_sha = _sha256_of_file(RAW_USGS_PATH)
            if p_sha == cfg.get("pressure_sha256") and u_sha == cfg.get("usgs_sha256"):
                logger.info("Existing files match checksums in config.yaml.")
                needs_download = False
            else:
                logger.info("Checksum mismatch. Re-downloading...")
                needs_download = True

        if needs_download:
            # Download pressure data
            download_noaa_pressure()

            # Download USGS catalog and capture row count
            usgs_row_count = fetch_usgs_data()

            # Verify pressure record count (no strict expectation; just record it)
            pressure_record_count = _count_pressure_records()
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
            # Use existing metadata from config
            pressure_record_count = cfg.get("pressure_record_count", 0)
            usgs_row_count = cfg.get("expected_earthquake_count", 0)

        # Final verification – ensure files exist
        if not (RAW_PRESSURE_PATH.exists() and RAW_USGS_PATH.exists()):
            raise FileNotFoundError("One or more raw data files are missing after download step.")

        # Verify that the pressure file has a non‑zero time dimension
        final_pressure_count = _count_pressure_records()
        if final_pressure_count <= 0:
            raise ValueError("Pressure dataset contains no time records.")

        # Verify USGS row count tolerance (±1% of expected, if we have an expectation)
        df_usgs = pd.read_csv(RAW_USGS_PATH)
        actual_usgs_count = len(df_usgs)
        expected_usgs_count = cfg.get("expected_earthquake_count", 0)
        if expected_usgs_count > 0:
            diff = abs(actual_usgs_count - expected_usgs_count)
            if diff > (0.01 * expected_usgs_count):
                raise ValueError(
                    f"USGS row count out of tolerance: expected {expected_usgs_count}, got {actual_usgs_count}"
                )

        # Write success log
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "w", encoding="utf-8") as log_f:
            log_f.write(f"Pressure data downloaded: {final_pressure_count} days\\n")
            log_f.write(f"USGS catalog rows: {actual_usgs_count}\\n")

        logger.info(
            f"T002 completed successfully - pressure records: {final_pressure_count}, USGS rows: {actual_usgs_count}"
        )
        return 0
    except Exception as e:
        logger.critical(f"T002 failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
