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
    "pressure_record_count": 4010,
    "moving_average_days": 30,
    "min_permutation_iterations": 1000,
    "max_permutation_iterations": 10000,
    "convergence_variance_threshold": 1e-5
}

def get_robust_session() -> requests.Session:
    """Create a requests session with retries to handle transient errors."""
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
    session.headers.update({"User-Agent": "llmXive-research-bot/1.0"})
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
    url = "https://huggingface.co/datasets/noaa/ncep-reanalysis-pressures/resolve/main/mslp_daily.nc"
    session = get_robust_session()
    try:
        logger.info(f"Downloading NOAA pressure dataset from {url}")
        with session.get(url, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(RAW_PRESSURE_PATH, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        logger.info("Pressure dataset download complete.")
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
        with session.get(base_url, params=params, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(RAW_USGS_PATH, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        df = pd.read_csv(RAW_USGS_PATH)
        logger.info(f"USGS catalog download complete, rows: {len(df)}")
        return len(df)
    except Exception as e:
        logger.error(f"Failed to fetch USGS data: {e}")
        raise RuntimeError(f"Critical failure fetching USGS data: {e}")

def _count_pressure_records() -> int:
    """Open the downloaded NetCDF file and return the number of time records."""
    with xr.open_dataset(RAW_PRESSURE_PATH, engine="netcdf4") as ds:
        count = int(ds.sizes.get("time", 0))
    return count

def main() -> int:
    logger.info("Starting T002: Data Acquisition Pipeline.")
    try:
        # 1. Check existing files and checksums
        cfg = load_config()
        files_ok = True
        if RAW_PRESSURE_PATH.exists() and RAW_USGS_PATH.exists():
            p_sha = _sha256_of_file(RAW_PRESSURE_PATH)
            u_sha = _sha256_of_file(RAW_USGS_PATH)
            if p_sha == cfg.get("pressure_sha256") and u_sha == cfg.get("usgs_sha256"):
                logger.info("Existing files match checksums in config.yaml.")
                files_ok = True
            else:
                logger.info("Checksum mismatch. Re-downloading...")
                files_ok = False
        else:
            files_ok = False

        if not files_ok:
            download_noaa_pressure()
            usgs_row_count = fetch_usgs_data()
            
            pressure_record_count = _count_pressure_records()
            if pressure_record_count != 4010:
                raise ValueError(f"Pressure record count mismatch: expected 4010, got {pressure_record_count}")
            
            pressure_sha = _sha256_of_file(RAW_PRESSURE_PATH)
            usgs_sha = _sha256_of_file(RAW_USGS_PATH)
            
            cfg.update({
                "pilot_mode": False,
                "expected_global_pressure_files": 1,
                "expected_earthquake_count": usgs_row_count,
                "pressure_sha256": pressure_sha,
                "usgs_sha256": usgs_sha,
                "pressure_record_count": pressure_record_count,
                "moving_average_days": 30
            })
            save_config(cfg)
        else:
            # Use existing values from config
            pressure_record_count = cfg.get("pressure_record_count", 4010)
            usgs_row_count = cfg.get("expected_earthquake_count", 0)

        # 2. Final Verification
        if not (RAW_PRESSURE_PATH.exists() and RAW_USGS_PATH.exists()):
            raise FileNotFoundError("One or more raw data files are missing.")
        
        # 3. Write success log
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "w", encoding="utf-8") as log_f:
            log_f.write(f"Pressure data downloaded: {pressure_record_count} days\n")
            log_f.write(f"USGS catalog rows: {usgs_row_count}\n")

        logger.info(f"T002 completed successfully - records: {pressure_record_count}, rows: {usgs_row_count}")
        return 0
    except Exception as e:
        logger.critical(f"T002 failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())