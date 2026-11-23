"""
Data Download Task (T013)
Conditional execution based on mode flag from verified_source_manifest.json.
Downloads real data if mode is 'Primary', otherwise skips and exits cleanly.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.logging_setup import get_logger
from utils.io_helpers import load_json, write_json

# Configure logger
logger = get_logger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
MANIFEST_PATH = PROJECT_ROOT / "data" / "verified_source_manifest.json"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
MODE_FLAG_KEY = "mode_flag"
STATUS_KEY = "status"
DATASET_URL_KEY = "dataset_url"
DATASET_ID_KEY = "dataset_id"

def load_manifest() -> Dict[str, Any]:
    """Load the verified source manifest."""
    if not MANIFEST_PATH.exists():
        logger.error(f"Manifest file not found: {MANIFEST_PATH}")
        raise FileNotFoundError(f"Manifest file not found: {MANIFEST_PATH}")
    
    return load_json(MANIFEST_PATH)

def check_mode(manifest: Dict[str, Any]) -> str:
    """
    Check the mode flag from the manifest.
    Returns 'Primary', 'Data Insufficient', 'Underpowered', or 'absent'.
    """
    status = manifest.get(STATUS_KEY, "absent")
    mode = manifest.get(MODE_FLAG_KEY, "Data Insufficient")
    
    logger.info(f"Manifest Status: {status}, Mode Flag: {mode}")
    
    if status == "absent" or mode == "Data Insufficient" or mode == "Underpowered":
        return mode
    
    return "Primary"

def download_dataset(manifest: Dict[str, Any]) -> bool:
    """
    Download the dataset identified in the manifest.
    Uses OpenNeuro as the primary source if available.
    Falls back to direct URL if provided.
    
    Returns True if download successful, False otherwise.
    """
    dataset_id = manifest.get(DATASET_ID_KEY)
    dataset_url = manifest.get(DATASET_URL_KEY)
    
    if not dataset_id and not dataset_url:
        logger.warning("No dataset ID or URL found in manifest. Skipping download.")
        return False

    # Ensure data/raw directory exists
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # Try OpenNeuro CLI first if dataset_id is present
    if dataset_id:
        try:
            logger.info(f"Attempting to download dataset {dataset_id} from OpenNeuro...")
            import subprocess
            
            # Use dcm2niix or deno openneuro if available, otherwise try direct git clone
            # OpenNeuro datasets are typically prefixed with 'ds'
            if not dataset_id.startswith('ds'):
                dataset_id = f"ds{dataset_id}"
            
            # Try using git-annex (standard for OpenNeuro)
            cmd = [
                "git", "clone", 
                "--depth", "1",
                f"https://github.com/OpenNeuroDatasets/{dataset_id}.git",
                str(DATA_RAW_DIR / dataset_id)
            ]
            
            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                logger.info(f"Successfully downloaded {dataset_id} to {DATA_RAW_DIR}")
                return True
            else:
                logger.warning(f"Git clone failed: {result.stderr}")
                # Try alternative: download specific subjects via openneuro-py if available
                logger.info("Trying alternative download method...")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Download timed out after 10 minutes.")
            return False
        except FileNotFoundError:
            logger.error("Git not found. Cannot download from OpenNeuro.")
            return False
        except Exception as e:
            logger.error(f"Error during OpenNeuro download: {e}")
            return False

    # Fallback to direct URL download if provided
    if dataset_url:
        try:
            logger.info(f"Attempting to download from URL: {dataset_url}")
            import urllib.request
            import tempfile
            
            filename = dataset_url.split('/')[-1]
            if not filename.endswith('.edf'):
                filename = f"sub-unknown_run-01.edf"
            
            output_path = DATA_RAW_DIR / filename
            logger.info(f"Saving to: {output_path}")
            
            # Use urllib to download
            urllib.request.urlretrieve(dataset_url, output_path)
            
            if output_path.exists() and output_path.stat().st_size > 0:
                logger.info(f"Successfully downloaded {filename}")
                return True
            else:
                logger.error("Downloaded file is empty or not created.")
                return False
                
        except Exception as e:
            logger.error(f"Error downloading from URL: {e}")
            return False

    return False

def main():
    """Main entry point for T013."""
    logger.info("Starting T013: Data Download Task")
    
    try:
        # Load manifest
        manifest = load_manifest()
        
        # Check mode
        mode = check_mode(manifest)
        
        if mode != "Primary":
            logger.info(f"Mode is '{mode}'. Skipping data download as per specification.")
            logger.info("T013 completed (skipped due to mode).")
            return 0
        
        # Attempt download
        logger.info("Mode is 'Primary'. Proceeding with data download...")
        success = download_dataset(manifest)
        
        if success:
            logger.info("T013 completed successfully. Data downloaded.")
            return 0
        else:
            logger.error("Data download failed. Updating manifest status to 'absent'.")
            
            # Update manifest to reflect failure
            manifest[STATUS_KEY] = "absent"
            manifest[MODE_FLAG_KEY] = "Data Insufficient"
            write_json(manifest, MANIFEST_PATH)
            
            logger.info("Manifest updated. Pipeline will terminate downstream tasks.")
            return 1
            
    except FileNotFoundError as e:
        logger.error(f"Manifest not found: {e}")
        logger.error("T013 cannot proceed without manifest.")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error in T013: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
