"""
Task T005c: Fetch Checksum Manifest.

Logic: Fetch manifest.json from the canonical HuggingFace source to data/raw/manifest.json.
Command: curl -L https://huggingface.co/datasets/agenticsts/trajectories/raw/main/manifest.json -o data/raw/manifest.json
Output: data/raw/manifest.json
Depends on: None.
"""
import os
import sys
import json
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
MANIFEST_URL = "https://huggingface.co/datasets/agenticsts/trajectories/raw/main/manifest.json"
MANIFEST_PATH = DATA_RAW_DIR / "manifest.json"


def fetch_manifest():
    """Fetch the manifest file from HuggingFace."""
    # Ensure directory exists
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    if MANIFEST_PATH.exists():
        logger.info(f"Manifest already exists at {MANIFEST_PATH}. Skipping download.")
        return True
    
    logger.info(f"Fetching manifest from {MANIFEST_URL}")
    logger.info(f"Target path: {MANIFEST_PATH}")
    
    try:
        # Use curl to fetch the manifest
        cmd = [
            "curl", "-L",
            MANIFEST_URL,
            "-o", str(MANIFEST_PATH)
        ]
        
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if not MANIFEST_PATH.exists():
            raise FileNotFoundError("Curl reported success but file was not created")
        
        # Validate JSON
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                logger.info(f"Manifest fetched and validated. Contains {len(data.get('files', []))} files.")
                return True
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in manifest: {e}")
                MANIFEST_PATH.unlink()
                raise ValueError(f"Manifest validation failed: {e}")
                
    except subprocess.CalledProcessError as e:
        logger.error(f"HTTP Error during fetch: {e.stderr}")
        if MANIFEST_PATH.exists():
            MANIFEST_PATH.unlink()
        raise RuntimeError(f"Manifest fetch failed (HTTP {e.returncode}); pipeline cannot proceed.") from e
    except subprocess.TimeoutExpired:
        logger.error("Manifest fetch timed out")
        raise TimeoutError("Manifest fetch timed out")


def main():
    """Entry point for T005c."""
    logger.info("Starting T005c: Fetch Checksum Manifest")
    try:
        fetch_manifest()
        logger.info("T005c completed successfully")
    except Exception as e:
        logger.critical(f"T005c failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()