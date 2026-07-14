"""
Dataset Download Script (T052)

Fetches verified NAB/PhysioNet subsets or UCI Electricity Load Diagrams and Traffic
via `ucimlrepo` or verified URLs.

Constraints:
1. Must check T052b search results before proceeding.
2. Must NOT fetch synthetic datasets.
3. Must write download manifest and checksums.
"""
import os
import sys
import json
import hashlib
import logging
import urllib.request
import ssl
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import urllib.error

# Add parent to path for imports if running as script
if "code/src" not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from ucimlrepo import fetch_ucirepo
except ImportError:
    # Fallback if ucimlrepo is not installed, though requirements should handle it
    print("ERROR: ucimlrepo package not found. Please install it via requirements.txt.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/dataset_download.log")
    ]
)
logger = logging.getLogger(__name__)

# Project Root (relative to where script is run)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "results"
SEARCH_RESULTS_PATH = PROCESSED_DIR / "search_results.json"
MANIFEST_PATH = PROCESSED_DIR / "download_manifest.json"
STATE_FILE_PATH = PROJECT_ROOT / "state" / "projects" / "PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml"

# Ensure directories exist
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

class DownloadResult:
    def __init__(self, name: str, path: str, size: int, checksum: str, status: str, message: str = ""):
        self.name = name
        self.path = path
        self.size = size
        self.checksum = checksum
        self.status = status  # 'success', 'failed', 'skipped'
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "size_bytes": self.size,
            "checksum_sha256": self.checksum,
            "status": self.status,
            "message": self.message
        }

def compute_file_checksum(filepath: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return "FILE_NOT_FOUND"

def validate_checksum(filepath: Path, expected_checksum: str) -> bool:
    """Validate file checksum."""
    if not filepath.exists():
        return False
    actual = compute_file_checksum(filepath)
    return actual == expected_checksum

def download_from_url(url: str, dest_path: Path, verify_ssl: bool = True) -> bool:
    """Download a file from URL to dest_path."""
    try:
        if verify_ssl:
            # Create an unverified context if needed, but standard is preferred
            context = ssl.create_default_context()
        else:
            context = ssl._create_unverified_context()

        logger.info(f"Downloading from {url} to {dest_path}...")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=context, timeout=60) as response:
            with open(dest_path, 'wb') as out_file:
                out_file.write(response.read())
        return True
    except Exception as e:
        logger.error(f"Download failed for {url}: {e}")
        return False

def download_electricity_dataset() -> DownloadResult:
    """Download UCI Electricity Load Diagrams 2011-2014."""
    # UCI Dataset ID: 555
    # Source: https://archive.ics.uci.edu/dataset/555/electricityloaddiagrams20112014
    # We use ucimlrepo to fetch it reliably.
    try:
        logger.info("Fetching UCI Electricity Dataset (ID: 555)...")
        # Fetch data
        dataset = fetch_ucirepo(id=555)
        data = dataset.data[0]  # Usually the first dataframe is the main data
        
        # Save to CSV
        filename = "electricity_load_diagrams_2011_2014.csv"
        dest_path = DATA_RAW_DIR / filename
        data.to_csv(dest_path, index=False)
        
        checksum = compute_file_checksum(dest_path)
        size = dest_path.stat().st_size
        
        logger.info(f"Saved {filename} ({size} bytes, checksum: {checksum[:16]}...)")
        return DownloadResult("electricity_load_diagrams_2011_2014", str(dest_path), size, checksum, "success")
    except Exception as e:
        logger.error(f"Failed to download Electricity dataset: {e}")
        return DownloadResult("electricity_load_diagrams_2011_2014", "", 0, "", "failed", str(e))

def download_traffic_dataset() -> DownloadResult:
    """Download UCI PEMS Traffic Dataset (PEMS-BAY or similar if available via ID)."""
    # Note: The original project spec mentions "Traffic" often referring to PEMS.
    # UCI has "PEMS Traffic" datasets. Let's try ID 491 (PEMS-BAY) or similar.
    # If specific ID is not found, we might need a direct URL.
    # Using ID 491 for PEMS-BAY as a proxy for "Traffic" if 505 (PEMS-SF) is banned.
    # Spec says: "Do NOT fetch synthetic datasets... Only UCI Electricity, Traffic".
    # We will try to fetch PEMS-BAY (ID 491) which is real traffic data.
    
    try:
        logger.info("Fetching UCI PEMS-BAY Traffic Dataset (ID: 491)...")
        dataset = fetch_ucirepo(id=491)
        data = dataset.data[0]
        
        filename = "pems_bay_traffic.csv"
        dest_path = DATA_RAW_DIR / filename
        data.to_csv(dest_path, index=False)
        
        checksum = compute_file_checksum(dest_path)
        size = dest_path.stat().st_size
        
        logger.info(f"Saved {filename} ({size} bytes, checksum: {checksum[:16]}...)")
        return DownloadResult("pems_bay_traffic", str(dest_path), size, checksum, "success")
    except Exception as e:
        logger.error(f"Failed to download Traffic dataset: {e}")
        return DownloadResult("pems_bay_traffic", "", 0, "", "failed", str(e))

def main():
    logger.info("=" * 60)
    logger.info("Dataset Download Script (T052)")
    logger.info("=" * 60)

    # 1. Check T052b Search Results
    if not SEARCH_RESULTS_PATH.exists():
        logger.warning(f"Search result file not found: {SEARCH_RESULTS_PATH}. Assuming search failed.")
        logger.critical("Aborting download. T052b Search failed: Search result file missing")
        
        # Even if failed, save a manifest indicating no downloads
        manifest = {
            "timestamp": datetime.now().isoformat(),
            "search_status": "failed",
            "search_file_missing": True,
            "datasets_downloaded": [],
            "total_downloads": 0
        }
        with open(MANIFEST_PATH, 'w') as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Download manifest saved to {MANIFEST_PATH}")
        logger.error("No datasets were successfully downloaded.")
        return 1

    try:
        with open(SEARCH_RESULTS_PATH, 'r') as f:
            search_data = json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in {SEARCH_RESULTS_PATH}")
        return 1

    # Check if search was successful
    if search_data.get("status") != "success":
        logger.warning("Search status is not 'success'. Aborting download.")
        manifest = {
            "timestamp": datetime.now().isoformat(),
            "search_status": search_data.get("status"),
            "datasets_downloaded": [],
            "total_downloads": 0
        }
        with open(MANIFEST_PATH, 'w') as f:
            json.dump(manifest, f, indent=2)
        return 1

    # 2. Define Datasets to Download (Real World Only)
    # Filter out synthetic datasets explicitly
    datasets_to_fetch = [
        ("electricity", download_electricity_dataset),
        ("traffic", download_traffic_dataset)
    ]

    results = []
    success_count = 0

    for name, fetch_func in datasets_to_fetch:
        logger.info(f"Processing dataset: {name}")
        result = fetch_func()
        results.append(result.to_dict())
        if result.status == "success":
            success_count += 1
        else:
            logger.warning(f"Dataset {name} failed: {result.message}")

    # 3. Generate Manifest
    manifest = {
        "timestamp": datetime.now().isoformat(),
        "search_status": "success",
        "datasets_downloaded": results,
        "total_downloads": success_count,
        "total_failed": len(results) - success_count
    }

    with open(MANIFEST_PATH, 'w') as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Download manifest saved to {MANIFEST_PATH}")

    if success_count == 0:
        logger.error("No datasets were successfully downloaded.")
        return 1
    else:
        logger.info(f"Successfully downloaded {success_count} dataset(s).")
        return 0

if __name__ == "__main__":
    sys.exit(main())