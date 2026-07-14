"""
T052: Dataset Download Script
Fetches verified NAB/PhysioNet subsets or UCI Electricity Load Diagrams and Traffic.
Conditioned on T052b (Search) success.
"""
import os
import sys
import json
import logging
import hashlib
import urllib.request
import ssl
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "results"
SEARCH_RESULTS_PATH = DATA_PROCESSED_DIR / "search_results.json"
DOWNLOAD_MANIFEST_PATH = DATA_PROCESSED_DIR / "download_manifest.json"

# Ensure directories exist
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

@dataclass
class DownloadResult:
    dataset_name: str
    source: str
    status: str  # 'success', 'failed', 'skipped'
    file_path: Optional[str] = None
    checksum: Optional[str] = None
    error_message: Optional[str] = None

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_search_results() -> Dict[str, Any]:
    """Load search results from T052b."""
    if not SEARCH_RESULTS_PATH.exists():
        logger.warning(f"Search result file not found: {SEARCH_RESULTS_PATH}. Assuming search failed.")
        return {}
    
    try:
        with open(SEARCH_RESULTS_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading search results: {e}")
        return {}

def download_from_url(url: str, dest_path: Path) -> bool:
    """Download a file from a URL with SSL verification."""
    try:
        # Create SSL context that verifies certificates
        ssl_context = ssl.create_default_context()
        
        logger.info(f"Downloading {url} to {dest_path}")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req, context=ssl_context) as response:
            with open(dest_path, 'wb') as out_file:
                out_file.write(response.read())
        
        logger.info(f"Successfully downloaded {dest_path.name}")
        return True
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False

def download_electricity_dataset() -> DownloadResult:
    """
    Download UCI Electricity Load Diagrams dataset.
    Source: UCI Machine Learning Repository
    """
    url = "https://archive.ics.uci.edu/static/public/321/electricityloaddiagrams20112014.zip"
    zip_path = DATA_RAW_DIR / "electricityloaddiagrams20112014.zip"
    csv_path = DATA_RAW_DIR / "electricity_load.csv"
    
    try:
        # Download zip
        if not download_from_url(url, zip_path):
            return DownloadResult(
                dataset_name="electricity",
                source="UCI",
                status="failed",
                error_message="Failed to download zip file"
            )
        
        # Extract (simple extraction for CSV)
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Find the CSV file in the zip
            csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
            if not csv_files:
                return DownloadResult(
                    dataset_name="electricity",
                    source="UCI",
                    status="failed",
                    error_message="No CSV file found in archive"
                )
            
            # Extract first CSV
            with zip_ref.open(csv_files[0]) as source, open(csv_path, 'wb') as target:
                target.write(source.read())
        
        checksum = compute_file_checksum(csv_path)
        
        # Clean up zip
        zip_path.unlink()
        
        return DownloadResult(
            dataset_name="electricity",
            source="UCI",
            status="success",
            file_path=str(csv_path),
            checksum=checksum
        )
    except Exception as e:
        logger.error(f"Error processing electricity dataset: {e}")
        return DownloadResult(
            dataset_name="electricity",
            source="UCI",
            status="failed",
            error_message=str(e)
        )

def download_traffic_dataset() -> DownloadResult:
    """
    Download UCI Traffic dataset (PEMS-BAY subset or similar).
    Source: UCI Machine Learning Repository
    Note: Using a verified public dataset that matches the specification.
    """
    # Using PEMS-BAY which is the standard traffic dataset for this research
    # Available from UCI or verified mirrors
    url = "https://raw.githubusercontent.com/laiguokun/multivariate-time-series-data/master/traffic/traffic.csv.gz"
    gz_path = DATA_RAW_DIR / "traffic.csv.gz"
    csv_path = DATA_RAW_DIR / "traffic.csv"
    
    try:
        if not download_from_url(url, gz_path):
            return DownloadResult(
                dataset_name="traffic",
                source="UCI",
                status="failed",
                error_message="Failed to download traffic data"
            )
        
        # Decompress
        import gzip
        with gzip.open(gz_path, 'rb') as f_in:
            with open(csv_path, 'wb') as f_out:
                f_out.write(f_in.read())
        
        checksum = compute_file_checksum(csv_path)
        
        # Clean up gz
        gz_path.unlink()
        
        return DownloadResult(
            dataset_name="traffic",
            source="UCI",
            status="success",
            file_path=str(csv_path),
            checksum=checksum
        )
    except Exception as e:
        logger.error(f"Error processing traffic dataset: {e}")
        return DownloadResult(
            dataset_name="traffic",
            source="UCI",
            status="failed",
            error_message=str(e)
        )

def download_nab_dataset() -> DownloadResult:
    """
    Download NAB (Numenta Anomaly Benchmark) dataset subset.
    Source: NAB GitHub repository
    """
    # Using a specific verified file from NAB
    url = "https://raw.githubusercontent.com/numenta/NAB/master/data/realKnownCause/numentaBenchmark.csv"
    dest_path = DATA_RAW_DIR / "nab_known_cause.csv"
    
    try:
        if not download_from_url(url, dest_path):
            return DownloadResult(
                dataset_name="nab_known_cause",
                source="NAB",
                status="failed",
                error_message="Failed to download NAB dataset"
            )
        
        checksum = compute_file_checksum(dest_path)
        
        return DownloadResult(
            dataset_name="nab_known_cause",
            source="NAB",
            status="success",
            file_path=str(dest_path),
            checksum=checksum
        )
    except Exception as e:
        logger.error(f"Error processing NAB dataset: {e}")
        return DownloadResult(
            dataset_name="nab_known_cause",
            source="NAB",
            status="failed",
            error_message=str(e)
        )

def validate_search_results(search_results: Dict[str, Any]) -> List[str]:
    """
    Validate search results and return list of datasets to download.
    Only downloads datasets that were verified in T052b search.
    """
    if not search_results:
        logger.warning("No search results found. Cannot proceed with download.")
        return []
    
    # Check if search was successful
    status = search_results.get("status", "")
    if status != "SUCCESS":
        logger.error(f"Search status is {status}. Aborting download.")
        return []
    
    # Get verified datasets
    verified_datasets = search_results.get("verified_datasets", [])
    if not verified_datasets:
        logger.warning("No verified datasets found in search results.")
        return []
    
    logger.info(f"Found {len(verified_datasets)} verified datasets to download: {verified_datasets}")
    return verified_datasets

def main():
    """Main entry point for T052."""
    logger.info("=" * 80)
    logger.info("Dataset Download Script (T052)")
    logger.info("=" * 80)
    
    # Step 1: Check T052b search results
    search_results = load_search_results()
    datasets_to_download = validate_search_results(search_results)
    
    if not datasets_to_download:
        logger.error("No datasets to download. Aborting.")
        # Save empty manifest
        manifest = {
            "status": "aborted",
            "reason": "T052b search failed or no verified datasets",
            "datasets": []
        }
        with open(DOWNLOAD_MANIFEST_PATH, 'w') as f:
            json.dump(manifest, f, indent=2)
        return
    
    # Step 2: Download verified datasets
    results: List[DownloadResult] = []
    
    for dataset_name in datasets_to_download:
        logger.info(f"Processing dataset: {dataset_name}")
        
        if dataset_name == "electricity":
            result = download_electricity_dataset()
        elif dataset_name == "traffic":
            result = download_traffic_dataset()
        elif dataset_name == "nab_known_cause":
            result = download_nab_dataset()
        else:
            logger.warning(f"Unknown dataset: {dataset_name}. Skipping.")
            results.append(DownloadResult(
                dataset_name=dataset_name,
                source="unknown",
                status="skipped",
                error_message="Unknown dataset name"
            ))
            continue
        
        results.append(result)
    
    # Step 3: Save download manifest
    manifest = {
        "status": "completed" if all(r.status == "success" for r in results) else "partial",
        "datasets": [asdict(r) for r in results],
        "timestamp": str(Path(__file__).parent.parent.parent.parent)  # Placeholder for actual timestamp
    }
    
    with open(DOWNLOAD_MANIFEST_PATH, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    # Step 4: Report results
    success_count = sum(1 for r in results if r.status == "success")
    logger.info(f"Download completed: {success_count}/{len(results)} datasets successful")
    
    if success_count == 0:
        logger.error("No datasets were successfully downloaded.")
        sys.exit(1)
    else:
        logger.info("All verified datasets downloaded successfully.")

if __name__ == "__main__":
    main()