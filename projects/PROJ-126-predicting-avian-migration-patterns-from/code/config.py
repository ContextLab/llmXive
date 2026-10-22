import os
import sys
import hashlib
import json
import logging
import random
from pathlib import Path
from datetime import datetime
import numpy as np

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW = DATA_DIR / "raw"
DATA_PROCESSED = DATA_DIR / "processed"
DATA_OUTPUTS = DATA_DIR / "outputs"

# Random Seed
RANDOM_SEED = 42

# Seed all RNGs
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

# Lake Powell Bounding Box (Approximate)
# Latitude: ~36.9 to 37.1, Longitude: ~-111.5 to -111.2
LAKE_POWELL_BOUNDS = {
    "min_lat": 36.9,
    "max_lat": 37.1,
    "min_lon": -111.5,
    "max_lon": -111.2
}

# Hyperparameters
HYPERPARAMETERS = {
    "max_depth": [3, 7],
    "eta": [0.01, 0.1],
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "n_estimators": 100
}

# Logging Configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = logging.INFO

def setup_logging():
    logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
    return logging.getLogger(__name__)

def get_logger(name):
    return logging.getLogger(name)

def ensure_directories():
    """Ensure all required data directories exist."""
    for directory in [DATA_RAW, DATA_PROCESSED, DATA_OUTPUTS]:
        directory.mkdir(parents=True, exist_ok=True)
        logging.info(f"Ensured directory: {directory}")

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_all_files_in_directory(directory: Path) -> list:
    """Get all files in a directory recursively."""
    return list(directory.rglob("*"))

def generate_checksums_for_raw_data():
    """Generate checksums for all files in data/raw."""
    files = get_all_files_in_directory(DATA_RAW)
    checksums = {}
    for file in files:
        if file.is_file():
          checksums[str(file.relative_to(DATA_RAW))] = calculate_sha256(file)
    return checksums

def save_checksums(checksums: dict, output_path: Path = DATA_RAW / "checksums.json"):
    """Save checksums to a JSON file."""
    with open(output_path, "w") as f:
        json.dump(checksums, f, indent=2)
    logging.info(f"Checksums saved to {output_path}")

def verify_checksums():
    """Verify checksums of raw data files."""
    checksum_file = DATA_RAW / "checksums.json"
    if not checksum_file.exists():
        logging.warning("Checksum file not found. Cannot verify.")
        return False
    
    with open(checksum_file, "r") as f:
        stored_checksums = json.load(f)
    
    for rel_path, stored_hash in stored_checksums.items():
        file_path = DATA_RAW / rel_path
        if not file_path.exists():
            logging.error(f"File missing: {file_path}")
            return False
        
        current_hash = calculate_sha256(file_path)
        if current_hash != stored_hash:
            logging.error(f"Checksum mismatch for {file_path}")
            return False
    
    logging.info("All checksums verified successfully.")
    return True

def setup_data_directories_and_verify():
    """Setup directories and verify checksums if they exist."""
    ensure_directories()
    if (DATA_RAW / "checksums.json").exists():
        verify_checksums()
    else:
        logging.info("No checksums found. Skipping verification.")

# ------------------------------------------------------------
# Additional configuration constants required by T001
# ------------------------------------------------------------

# Base data root (relative to this file)
DATA_ROOT = Path(__file__).parents[1] / "data"

# Sub‑directories
RAW_DIR = DATA_ROOT / "raw"
PROC_DIR = DATA_ROOT / "processed"
OUT_DIR = DATA_ROOT / "outputs"

# Regional bounding box (Pacific Northwest)
REGIONAL_BBOX = (45, 50, -125, -115)   # (min_lat, max_lat, min_lon, max_lon)

# Smaller regional subset used for fallback
REGIONAL_SUBSET = (47, 48, -121, -120)

# XGBoost hyper‑parameters for model training
XGB_PARAMS = {
    "max_depth": 6,
    "n_estimators": 200,
    "learning_rate": 0.1,
    "objective": "reg:squarederror",
    "n_jobs": 2,
    "tree_method": "hist"
}

# Thresholds for cumulative‑count sweep
THRESHOLDS = [3, 5, 10]

# Maximum allowed gap (in days) for temporal interpolation of MODIS data
MAX_GAP_DAYS = 7

# Resource limits for the pipeline
RAM_LIMIT_GB = 7
TIME_LIMIT_HOURS = 6

# Ensure directories exist at import time (idempotent)
for _dir in (RAW_DIR, PROC_DIR, OUT_DIR):
    _dir.mkdir(parents=True, exist_ok=True)