import os
import sys
import json
import logging
import hashlib
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_URL = "https://huggingface.co/datasets/agenticsts/trajectories/raw/main"
MANIFEST_URL = f"{BASE_URL}/manifest.json"
DATA_URL = f"{BASE_URL}/agenticsts_trajectories.jsonl"
RAW_DIR = Path("data/raw")
MANIFEST_PATH = RAW_DIR / "manifest.json"
DATA_PATH = RAW_DIR / "agenticsts_trajectories.jsonl"

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def fetch_manifest() -> Dict[str, Any]:
    """Fetch and validate the manifest.json file."""
    logger.info(f"Fetching manifest from {MANIFEST_URL}")
    try:
        with urllib.request.urlopen(MANIFEST_URL, timeout=30) as response:
            manifest_data = json.loads(response.read().decode('utf-8'))
        
        # Save manifest locally
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
            json.dump(manifest_data, f, indent=2)
        
        logger.info(f"Manifest saved to {MANIFEST_PATH}")
        return manifest_data
    except urllib.error.URLError as e:
        logger.error(f"Failed to fetch manifest: {e}")
        raise FileNotFoundError(f"Cannot fetch manifest from HuggingFace: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in manifest: {e}")
        raise ValueError(f"Manifest JSON is invalid: {e}")

def download_real_data() -> None:
    """Download the real trajectory data from HuggingFace."""
    logger.info(f"Downloading trajectories from {DATA_URL}")
    
    # Ensure directory exists
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        # Use a chunked download for large files
        with urllib.request.urlopen(DATA_URL, timeout=60) as response:
            total_size = int(response.headers.get('content-length', 0))
            block_size = 8192
            downloaded = 0
            
            with open(DATA_PATH, 'wb') as f:
                while True:
                    chunk = response.read(block_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        logger.info(f"Download progress: {progress:.1f}%")
        
        logger.info(f"Data downloaded to {DATA_PATH}")
    except urllib.error.URLError as e:
        logger.error(f"Failed to download data: {e}")
        raise FileNotFoundError(f"Cannot download data from HuggingFace: {e}")
    except Exception as e:
        logger.error(f"Error during download: {e}")
        raise RuntimeError(f"Download failed: {e}")

def verify_checksum(manifest: Dict[str, Any]) -> bool:
    """Verify the downloaded file against the manifest checksum."""
    if not DATA_PATH.exists():
        logger.error(f"Data file not found: {DATA_PATH}")
        return False
    
    expected_checksum = manifest.get('checksums', {}).get('agenticsts_trajectories.jsonl')
    if not expected_checksum:
        logger.error("Expected checksum not found in manifest")
        return False
    
    actual_checksum = compute_sha256(DATA_PATH)
    
    if actual_checksum != expected_checksum:
        logger.error(f"Checksum mismatch!")
        logger.error(f"  Expected: {expected_checksum}")
        logger.error(f"  Actual:   {actual_checksum}")
        logger.error("Pipeline aborted due to checksum failure.")
        return False
    
    logger.info(f"Checksum verified: {actual_checksum}")
    return True

def main() -> None:
    """Main entry point for T005b."""
    logger.info("Starting T005b: Ingest Real AgenticSTS Trajectories")
    
    # Check if data already exists and skip if valid
    if DATA_PATH.exists():
        logger.info(f"Data file already exists: {DATA_PATH}")
        # Fetch manifest to verify checksum
        try:
            manifest = fetch_manifest()
            if verify_checksum(manifest):
                logger.info("Existing data verified. Skipping download.")
                return
            else:
                logger.warning("Existing data checksum mismatch. Re-downloading...")
                DATA_PATH.unlink()
        except Exception as e:
            logger.warning(f"Could not verify existing data: {e}. Re-downloading...")
            DATA_PATH.unlink()
    
    # Fetch manifest first
    manifest = fetch_manifest()
    
    # Download real data
    download_real_data()
    
    # Verify checksum
    if not verify_checksum(manifest):
        raise FileNotFoundError(
            "Real data ingestion failed: checksum verification failed. "
            "Pipeline cannot proceed without valid data."
        )
    
    logger.info("T005b completed successfully.")

if __name__ == "__main__":
    main()
