"""
Dataset Download and Verification Script (T052/T059)

This script handles:
1. Searching for verified real-world datasets (T052b logic check)
2. Downloading datasets if search was successful
3. Verifying dataset integrity against checksums (T059)

Usage:
    python code/src/data/download_datasets.py
"""

import os
import sys
import json
import hashlib
import logging
import urllib.request
import ssl
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_RESULTS_DIR = PROJECT_ROOT / "data" / "processed" / "results"
STATE_DIR = PROJECT_ROOT / "state" / "projects"
SEARCH_RESULTS_FILE = PROCESSED_RESULTS_DIR / "search_results.json"
DOWNLOAD_MANIFEST_FILE = PROCESSED_RESULTS_DIR / "download_manifest.json"
STATE_FILE = STATE_DIR / "PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml"

@dataclass
class DownloadResult:
    dataset_name: str
    file_path: str
    checksum: str
    size_bytes: int
    status: str  # 'success', 'failed', 'skipped'
    error_message: Optional[str] = None

def compute_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        raise IOError(f"Failed to compute checksum for {file_path}: {e}")

def validate_checksum(file_path: Path, expected_checksum: str) -> bool:
    """Validate file checksum against expected value."""
    if not file_path.exists():
        return False
    computed = compute_file_checksum(file_path)
    return computed.lower() == expected_checksum.lower()

def load_checksum_cache() -> Dict[str, str]:
    """Load existing checksum cache from state file."""
    if not STATE_FILE.exists():
        logger.warning(f"State file not found: {STATE_FILE}")
        return {}
    
    try:
        import yaml
        with open(STATE_FILE, 'r') as f:
            state_data = yaml.safe_load(f)
        
        checksums = {}
        if 'artifacts' in state_data:
            for artifact in state_data['artifacts']:
                if 'checksum' in artifact and 'path' in artifact:
                    # Normalize path for comparison
                    rel_path = Path(artifact['path'])
                    # Check if it's a data file
                    if str(rel_path).startswith('data/'):
                        checksums[str(rel_path)] = artifact['checksum']
        return checksums
    except Exception as e:
        logger.error(f"Failed to load checksum cache: {e}")
        return {}

def save_checksum_cache(checksums: Dict[str, str]):
    """Save checksum cache to state file."""
    try:
        import yaml
        
        # Load existing state or create new
        state_data = {'artifacts': []}
        if STATE_FILE.exists():
            with open(STATE_FILE, 'r') as f:
                state_data = yaml.safe_load(f) or {'artifacts': []}
        
        # Update or add checksums
        existing_paths = {a.get('path') for a in state_data.get('artifacts', [])}
        
        for path, checksum in checksums.items():
            path_obj = Path(path)
            if path_obj.exists():
                # Check if artifact already exists
                found = False
                for artifact in state_data.get('artifacts', []):
                    if artifact.get('path') == path:
                        artifact['checksum'] = checksum
                        artifact['size_bytes'] = path_obj.stat().st_size
                        found = True
                        break
                
                if not found:
                    state_data['artifacts'].append({
                        'path': path,
                        'checksum': checksum,
                        'size_bytes': path_obj.stat().st_size,
                        'type': 'data_file'
                    })
        
        # Save updated state
        with open(STATE_FILE, 'w') as f:
            yaml.dump(state_data, f, default_flow_style=False)
        
        logger.info(f"Updated checksum cache in {STATE_FILE}")
    except Exception as e:
        logger.error(f"Failed to save checksum cache: {e}")

def download_from_url(url: str, dest_path: Path) -> bool:
    """Download file from URL with SSL verification."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Create SSL context that verifies certificates
        ssl_context = ssl.create_default_context()
        
        logger.info(f"Downloading {url} to {dest_path}")
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; ResearchBot/1.0)'}
        )
        
        with urllib.request.urlopen(req, context=ssl_context, timeout=60) as response:
            with open(dest_path, 'wb') as out_file:
                # Download in chunks
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    out_file.write(chunk)
        
        logger.info(f"Downloaded {dest_path} ({dest_path.stat().st_size} bytes)")
        return True
    except Exception as e:
        logger.error(f"Download failed for {url}: {e}")
        return False

def download_electricity_dataset() -> Optional[DownloadResult]:
    """Download UCI Electricity Load Diagrams dataset."""
    # Verified source: UCI Machine Learning Repository
    url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00321/LD2011_2014.txt.zip"
    dest_path = DATA_RAW_DIR / "electricity_load_diagrams.csv"
    zip_path = DATA_RAW_DIR / "electricity_load_diagrams.csv.zip"
    
    if not download_from_url(url, zip_path):
        return None
    
    # Extract CSV (simplified for this implementation)
    try:
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Find the CSV file in the zip
            csv_files = [f for f in zip_ref.namelist() if f.endswith('.txt')]
            if csv_files:
                zip_ref.extract(csv_files[0], DATA_RAW_DIR)
                extracted_path = DATA_RAW_DIR / csv_files[0]
                # Rename to standard name
                extracted_path.rename(dest_path)
                os.remove(zip_path)
                logger.info(f"Extracted to {dest_path}")
    except Exception as e:
        logger.error(f"Failed to extract electricity dataset: {e}")
        if zip_path.exists():
            zip_path.unlink()
        return None
    
    return DownloadResult(
        dataset_name="electricity",
        file_path=str(dest_path),
        checksum=compute_file_checksum(dest_path),
        size_bytes=dest_path.stat().st_size,
        status="success"
    )

def download_traffic_dataset() -> Optional[DownloadResult]:
    """Download UCI Traffic dataset."""
    # Verified source: UCI Machine Learning Repository (PEMS)
    # Using a verified mirror for PEMS traffic data
    url = "https://archive.ics.uci.edu/static/public/220/data.zip"
    dest_path = DATA_RAW_DIR / "traffic.csv"
    zip_path = DATA_RAW_DIR / "traffic.csv.zip"
    
    if not download_from_url(url, zip_path):
        return None
    
    try:
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
            if csv_files:
                zip_ref.extract(csv_files[0], DATA_RAW_DIR)
                extracted_path = DATA_RAW_DIR / csv_files[0]
                extracted_path.rename(dest_path)
                os.remove(zip_path)
                logger.info(f"Extracted to {dest_path}")
    except Exception as e:
        logger.error(f"Failed to extract traffic dataset: {e}")
        if zip_path.exists():
            zip_path.unlink()
        return None
    
    return DownloadResult(
        dataset_name="traffic",
        file_path=str(dest_path),
        checksum=compute_file_checksum(dest_path),
        size_bytes=dest_path.stat().st_size,
        status="success"
    )

def verify_dataset_integrity(dataset_name: str, expected_checksum: str) -> bool:
    """
    T059: Verify dataset integrity against checksums before processing.
    
    This function checks if a dataset file exists and its checksum matches
    the expected value from the state file or provided expected checksum.
    
    Args:
        dataset_name: Name of the dataset (e.g., 'electricity', 'traffic')
        expected_checksum: Expected SHA256 checksum string
        
    Returns:
        bool: True if verification passes, False otherwise
        
    Raises:
        FileNotFoundError: If dataset file does not exist
        ValueError: If checksum does not match
    """
    # Map dataset names to file paths
    dataset_paths = {
        'electricity': DATA_RAW_DIR / "electricity_load_diagrams.csv",
        'traffic': DATA_RAW_DIR / "traffic.csv"
    }
    
    if dataset_name not in dataset_paths:
        raise ValueError(f"Unknown dataset: {dataset_name}")
    
    file_path = dataset_paths[dataset_name]
    
    if not file_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {file_path}")
    
    # Compute actual checksum
    actual_checksum = compute_file_checksum(file_path)
    
    # Compare checksums (case-insensitive)
    if actual_checksum.lower() != expected_checksum.lower():
        raise ValueError(
            f"Checksum mismatch for {dataset_name}:\n"
            f"  Expected: {expected_checksum}\n"
            f"  Actual:   {actual_checksum}"
        )
    
    logger.info(f"✓ Integrity verified for {dataset_name}: {actual_checksum[:16]}...")
    return True

def download_all_datasets() -> List[DownloadResult]:
    """Download all verified datasets and return results."""
    results = []
    
    # Try electricity
    logger.info("Attempting to download Electricity dataset...")
    result = download_electricity_dataset()
    if result:
        results.append(result)
    
    # Try traffic
    logger.info("Attempting to download Traffic dataset...")
    result = download_traffic_dataset()
    if result:
        results.append(result)
    
    return results

def main():
    """Main entry point for dataset download and verification."""
    logger.info("=" * 80)
    logger.info("Dataset Download and Verification Script (T052/T059)")
    logger.info("=" * 80)
    
    # Ensure directories exist
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check if search was successful (T052b)
    if not SEARCH_RESULTS_FILE.exists():
        logger.warning(f"Search result file not found: {SEARCH_RESULTS_FILE}")
        logger.warning("Assuming search failed. Aborting download.")
        
        # Create download manifest indicating failure
        manifest = {
            'status': 'aborted',
            'reason': 'T052b Search failed: Search result file missing',
            'timestamp': str(Path(__file__).stat().st_mtime)
        }
        with open(DOWNLOAD_MANIFEST_FILE, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"Download manifest saved to {DOWNLOAD_MANIFEST_FILE}")
        logger.error("No datasets were successfully downloaded.")
        return 1
    
    # Load search results
    try:
        with open(SEARCH_RESULTS_FILE, 'r') as f:
            search_results = json.load(f)
        
        if search_results.get('status') != 'success':
            logger.warning(f"Search failed: {search_results.get('reason', 'Unknown reason')}")
            logger.warning("Aborting download.")
            
            manifest = {
                'status': 'aborted',
                'reason': f"T052b Search failed: {search_results.get('reason', 'Unknown')}",
                'timestamp': str(Path(__file__).stat().st_mtime)
            }
            with open(DOWNLOAD_MANIFEST_FILE, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            logger.info(f"Download manifest saved to {DOWNLOAD_MANIFEST_FILE}")
            logger.error("No datasets were successfully downloaded.")
            return 1
    except Exception as e:
        logger.error(f"Failed to load search results: {e}")
        logger.warning("Aborting download due to error.")
        return 1
    
    # Download datasets
    logger.info("Search successful. Proceeding with download...")
    download_results = download_all_datasets()
    
    # Verify downloaded datasets (T059)
    verified_results = []
    for result in download_results:
        try:
            # Load expected checksums from state file
            checksum_cache = load_checksum_cache()
            expected_checksum = checksum_cache.get(result.file_path)
            
            if expected_checksum:
                # Verify against cached checksum
                if validate_checksum(Path(result.file_path), expected_checksum):
                    logger.info(f"✓ Verified {result.dataset_name} against cached checksum")
                    result.status = 'verified'
                else:
                    logger.warning(f"⚠ Checksum mismatch for {result.dataset_name}")
                    result.status = 'failed'
                    result.error_message = "Checksum mismatch"
            else:
                # If no cached checksum, compute and save it
                logger.info(f"Computing checksum for new dataset: {result.dataset_name}")
                result.status = 'success'
            
            verified_results.append(result)
            
        except Exception as e:
            logger.error(f"Verification failed for {result.dataset_name}: {e}")
            result.status = 'failed'
            result.error_message = str(e)
            verified_results.append(result)
    
    # Save download manifest
    manifest = {
        'status': 'completed' if all(r.status in ['success', 'verified'] for r in verified_results) else 'partial',
        'timestamp': str(Path(__file__).stat().st_mtime),
        'datasets': [asdict(r) for r in verified_results]
    }
    
    with open(DOWNLOAD_MANIFEST_FILE, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Download manifest saved to {DOWNLOAD_MANIFEST_FILE}")
    
    # Update checksum cache with new datasets
    new_checksums = {r.file_path: r.checksum for r in verified_results if r.status in ['success', 'verified']}
    if new_checksums:
        save_checksum_cache(new_checksums)
    
    # Report summary
    success_count = sum(1 for r in verified_results if r.status in ['success', 'verified'])
    logger.info(f"Download complete: {success_count}/{len(verified_results)} datasets successful")
    
    if success_count == 0:
        logger.error("No datasets were successfully downloaded.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())