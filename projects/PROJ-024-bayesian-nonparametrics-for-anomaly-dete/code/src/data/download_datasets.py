"""
Download verified real-world datasets for anomaly detection research.

This script fetches datasets from verified sources:
- NAB (Numenta Anomaly Benchmark)
- PhysioNet
- UCI Machine Learning Repository (Electricity, Traffic)

It checks the outcome of T052b (search procedure) before attempting downloads.
If T052b failed (no verified source found), this script exits without downloading.
"""

import os
import sys
import hashlib
import logging
import urllib.request
import ssl
import json
from pathlib import Path
from typing import Optional, Dict, Tuple
from dataclasses import dataclass

# Try to import ucimlrepo for UCI datasets
try:
    from ucimlrepo import fetch_ucirepo
    UCIML_AVAILABLE = True
except ImportError:
    UCIML_AVAILABLE = False
    logging.warning("ucimlrepo not available. UCI datasets will be downloaded via direct URLs.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/data_download.log')
    ]
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
STATE_DIR = PROJECT_ROOT / "state" / "projects"
PROJECT_STATE_FILE = STATE_DIR / "PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml"
T052B_RESULT_FILE = PROJECT_ROOT / "data" / "processed" / "results" / "validation_deferred.md"
CHECKSUM_CACHE_FILE = PROJECT_ROOT / "state" / "checksums.json"

@dataclass
class DownloadResult:
    dataset_name: str
    success: bool
    file_path: Optional[str]
    checksum: Optional[str]
    error_message: Optional[str] = None

def compute_file_checksum(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_checksum_cache() -> Dict:
    """Load existing checksum cache."""
    if CHECKSUM_CACHE_FILE.exists():
        with open(CHECKSUM_CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_checksum_cache(cache: Dict):
    """Save checksum cache to file."""
    with open(CHECKSUM_CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)

def check_t052b_status() -> bool:
    """
    Check if T052b (search procedure) was successful.
    Returns True if T052b succeeded (verified sources found), False if it failed.
    """
    if T052B_RESULT_FILE.exists():
        # Read the deferred report to check status
        with open(T052B_RESULT_FILE, 'r') as f:
            content = f.read()
            if 'status: DEFERRED' in content:
                logger.info("T052b search procedure failed - no verified sources found. Aborting download.")
                return False
    return True

def download_from_url(url: str, output_path: str) -> Tuple[bool, str]:
    """
    Download a file from URL with SSL verification.
    Returns (success, error_message).
    """
    try:
        # Create SSL context that verifies certificates
        ssl_context = ssl.create_default_context()
        
        # For some UCI URLs that might have certificate issues, we can be more lenient
        # but still verify the connection
        if "archive.ics.uci.edu" in url or "github.com" in url:
            # Use default SSL context for these trusted sources
            pass
        
        logger.info(f"Downloading from {url} to {output_path}")
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Download the file
        request = urllib.request.Request(url)
        request.add_header('User-Agent', 'Mozilla/5.0 (Research Bot)')
        
        with urllib.request.urlopen(request, context=ssl_context, timeout=30) as response:
            with open(output_path, 'wb') as out_file:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    out_file.write(chunk)
        
        return True, ""
    except Exception as e:
        return False, str(e)

def download_electricity_dataset() -> DownloadResult:
    """Download UCI Electricity Load Diagrams dataset."""
    output_path = str(DATA_RAW_DIR / "electricity.csv")
    
    # Try using ucimlrepo first if available
    if UCIML_AVAILABLE:
        try:
            logger.info("Attempting to download Electricity dataset via ucimlrepo...")
            electricity = fetch_ucirepo(id=321)
            data = electricity.data[0]  # First dataset
            data.to_csv(output_path, index=False)
            checksum = compute_file_checksum(output_path)
            logger.info(f"Electricity dataset downloaded successfully via ucimlrepo. Checksum: {checksum[:16]}...")
            return DownloadResult("electricity", True, output_path, checksum)
        except Exception as e:
            logger.warning(f"ucimlrepo download failed: {e}. Trying direct URL...")
    
    # Fallback to direct URL download
    url = "https://archive.ics.uci.edu/static/public/321/electricityloaddiagrams20112014.zip"
    temp_zip = str(DATA_RAW_DIR / "electricity_temp.zip")
    
    success, error = download_from_url(url, temp_zip)
    if not success:
        logger.error(f"Electricity download failed: {error}")
        return DownloadResult("electricity", False, None, None, error)
    
    # Extract the CSV from the zip file
    import zipfile
    try:
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            # Find CSV files in the archive
            csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
            if csv_files:
                with zip_ref.open(csv_files[0]) as csv_file:
                    with open(output_path, 'wb') as out_file:
                        out_file.write(csv_file.read())
                os.remove(temp_zip)
                checksum = compute_file_checksum(output_path)
                logger.info(f"Electricity dataset downloaded and extracted. Checksum: {checksum[:16]}...")
                return DownloadResult("electricity", True, output_path, checksum)
            else:
                os.remove(temp_zip)
                return DownloadResult("electricity", False, None, None, "No CSV file found in archive")
    except Exception as e:
        if os.path.exists(temp_zip):
            os.remove(temp_zip)
        return DownloadResult("electricity", False, None, None, str(e))

def download_traffic_dataset() -> DownloadResult:
    """Download UCI Traffic dataset."""
    output_path = str(DATA_RAW_DIR / "traffic.csv")
    
    # Try using ucimlrepo first if available
    if UCIML_AVAILABLE:
        try:
            logger.info("Attempting to download Traffic dataset via ucimlrepo...")
            traffic = fetch_ucirepo(id=363)
            data = traffic.data[0]  # First dataset
            data.to_csv(output_path, index=False)
            checksum = compute_file_checksum(output_path)
            logger.info(f"Traffic dataset downloaded successfully via ucimlrepo. Checksum: {checksum[:16]}...")
            return DownloadResult("traffic", True, output_path, checksum)
        except Exception as e:
            logger.warning(f"ucimlrepo download failed: {e}. Trying direct URL...")
    
    # Fallback to direct URL download
    url = "https://archive.ics.uci.edu/static/public/363/traffic_data.zip"
    temp_zip = str(DATA_RAW_DIR / "traffic_temp.zip")
    
    success, error = download_from_url(url, temp_zip)
    if not success:
        logger.error(f"Traffic download failed: {error}")
        return DownloadResult("traffic", False, None, None, error)
    
    # Extract the CSV from the zip file
    import zipfile
    try:
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
            if csv_files:
                with zip_ref.open(csv_files[0]) as csv_file:
                    with open(output_path, 'wb') as out_file:
                        out_file.write(csv_file.read())
                os.remove(temp_zip)
                checksum = compute_file_checksum(output_path)
                logger.info(f"Traffic dataset downloaded and extracted. Checksum: {checksum[:16]}...")
                return DownloadResult("traffic", True, output_path, checksum)
            else:
                os.remove(temp_zip)
                return DownloadResult("traffic", False, None, None, "No CSV file found in archive")
    except Exception as e:
        if os.path.exists(temp_zip):
            os.remove(temp_zip)
        return DownloadResult("traffic", False, None, None, str(e))

def download_nab_dataset(dataset_name: str) -> DownloadResult:
    """
    Download dataset from Numenta Anomaly Benchmark.
    Note: NAB datasets are available via GitHub.
    """
    # NAB datasets are hosted on GitHub
    base_url = "https://raw.githubusercontent.com/numenta/NAB/master/data/realKnownCause/"
    url = base_url + dataset_name + ".csv"
    output_path = str(DATA_RAW_DIR / f"nab_{dataset_name}.csv")
    
    success, error = download_from_url(url, output_path)
    if success:
        checksum = compute_file_checksum(output_path)
        logger.info(f"NAB {dataset_name} dataset downloaded. Checksum: {checksum[:16]}...")
        return DownloadResult(f"nab_{dataset_name}", True, output_path, checksum)
    else:
        logger.error(f"NAB {dataset_name} download failed: {error}")
        return DownloadResult(f"nab_{dataset_name}", False, None, None, error)

def download_physionet_dataset(dataset_name: str) -> DownloadResult:
    """
    Download dataset from PhysioNet.
    Note: PhysioNet requires registration and may have access restrictions.
    This function attempts to download from open datasets.
    """
    # PhysioNet open datasets URL pattern
    base_url = "https://physionet.org/files/"
    # Example: https://physionet.org/files/challenge-2017/1.0.0/
    # This is a simplified example - actual implementation would need specific dataset URLs
    logger.warning(f"PhysioNet download for {dataset_name} requires manual verification and registration.")
    return DownloadResult(f"physionet_{dataset_name}", False, None, None, "Manual verification required for PhysioNet access")

def download_all_datasets() -> list:
    """
    Download all verified real-world datasets.
    Returns list of DownloadResult objects.
    """
    results = []
    
    # Check T052b status first
    if not check_t052b_status():
        logger.error("T052b search procedure failed. Aborting all downloads.")
        return results
    
    logger.info("Starting dataset downloads...")
    logger.info("=" * 60)
    
    # Download UCI Electricity dataset
    results.append(download_electricity_dataset())
    
    # Download UCI Traffic dataset
    results.append(download_traffic_dataset())
    
    # Download NAB datasets (realKnownCause subset)
    nab_datasets = ['artificialWithAnomaly', 'realAdmitted', 'realAssessed', 
                   'realKnownCause', 'realUsage', 'realWorld', 'realEcg']
    for nab_ds in nab_datasets:
        results.append(download_nab_dataset(nab_ds))
    
    # Log summary
    logger.info("=" * 60)
    logger.info("Download Summary:")
    logger.info("=" * 60)
    
    successful = 0
    failed = 0
    for result in results:
        status = "✓" if result.success else "✗"
        logger.info(f"  {result.dataset_name}: {status}")
        if result.success:
            successful += 1
        else:
            failed += 1
            if result.error_message:
                logger.info(f"    Error: {result.error_message}")
    
    logger.info("=" * 60)
    logger.info(f"Successful: {successful}, Failed: {failed}")
    logger.info("=" * 60)
    
    if failed > 0:
        logger.error("✗ Some downloads failed. Check error messages above.")
    else:
        logger.info("✓ All downloads completed successfully.")
    
    return results

def main():
    """Main entry point for dataset download script."""
    logger.info("Starting dataset download process...")
    
    # Ensure data directory exists
    os.makedirs(DATA_RAW_DIR, exist_ok=True)
    
    # Download all datasets
    results = download_all_datasets()
    
    # Save checksums
    if results:
        checksum_cache = load_checksum_cache()
        for result in results:
            if result.success and result.file_path:
                checksum_cache[result.dataset_name] = {
                    'checksum': result.checksum,
                    'file_path': result.file_path
                }
        save_checksum_cache(checksum_cache)
        logger.info("Saved checksum cache to " + str(CHECKSUM_CACHE_FILE))
    
    # Return success if at least one dataset was downloaded
    successful_downloads = [r for r in results if r.success]
    if successful_downloads:
        logger.info("✓ At least one dataset downloaded successfully.")
        sys.exit(0)
    else:
        logger.error("✗ No datasets were downloaded successfully.")
        sys.exit(1)

if __name__ == "__main__":
    main()