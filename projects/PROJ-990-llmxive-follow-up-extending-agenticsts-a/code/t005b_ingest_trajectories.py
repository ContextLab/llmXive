"""
Task T005b: Ingest Real AgenticSTS Trajectories.

Logic:
1. Fetch trajectories from the canonical HuggingFace dataset source using huggingface-cli.
2. Verify checksums against data/raw/manifest.json using sha256sum.
3. If checksum mismatch, raise FileNotFoundError.
4. Output: data/raw/agenticsts_trajectories.jsonl

Constraint: Must run BEFORE T006a.
Depends on: T005c (manifest.json must exist).
"""
import os
import sys
import json
import hashlib
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
MANIFEST_PATH = DATA_RAW_DIR / "manifest.json"
OUTPUT_FILE = DATA_RAW_DIR / "agenticsts_trajectories.jsonl"
DATASET_NAME = "agenticsts/trajectories"
REMOTE_FILENAME = "trajectories.jsonl"


def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Load and parse the manifest JSON file."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def verify_checksum(file_path: Path, expected_hash: str) -> bool:
    """Verify file checksum against expected hash."""
    computed_hash = compute_sha256(file_path)
    return computed_hash == expected_hash


def download_dataset(dataset_name: str, local_dir: Path, filename: str) -> Path:
    """
    Download dataset using huggingface-cli.
    
    Command: huggingface-cli download <dataset> --repo-type dataset --local-dir <dir> --filename <file>
    """
    if not local_dir.exists():
        local_dir.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        "huggingface-cli", "download",
        dataset_name,
        "--repo-type", "dataset",
        "--local-dir", str(local_dir),
        "--filename", filename
    ]
    
    logger.info(f"Executing: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout for large downloads
        )
        if result.stderr:
            logger.warning(f"Download stderr: {result.stderr}")
        
        output_path = local_dir / filename
        if not output_path.exists():
            # Handle case where huggingface-cli might use a different naming convention
            # or if the file is placed in a subdirectory
            for p in local_dir.rglob(filename):
                if p.is_file():
                    if p != output_path:
                        logger.info(f"Found downloaded file at: {p}, moving to {output_path}")
                        p.replace(output_path)
                    return output_path
            raise FileNotFoundError(f"Download completed but file not found at {output_path}")
        
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Download failed with return code {e.returncode}")
        logger.error(f"stderr: {e.stderr}")
        raise RuntimeError(f"huggingface-cli download failed: {e.stderr}") from e
    except subprocess.TimeoutExpired:
        raise TimeoutError("Download timed out after 1 hour")


def run_ingestion() -> Dict[str, Any]:
    """
    Main ingestion logic:
    1. Load manifest
    2. Check if file exists, if not download
    3. Verify checksum
    4. Return status
    """
    # Ensure directories exist
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load manifest
    logger.info(f"Loading manifest from {MANIFEST_PATH}")
    try:
        manifest = load_manifest(MANIFEST_PATH)
    except FileNotFoundError as e:
        logger.error(f"Manifest not found. Ensure T005c has run: {e}")
        raise
    
    # Find the trajectories file entry in manifest
    trajectories_entry = None
    for file_entry in manifest.get("files", []):
        if file_entry["name"] == REMOTE_FILENAME:
            trajectories_entry = file_entry
            break
    
    if not trajectories_entry:
        raise ValueError(f"File '{REMOTE_FILENAME}' not found in manifest")
    
    expected_hash = trajectories_entry["sha256"]
    logger.info(f"Expected checksum: {expected_hash}")
    
    # Check if file already exists
    if OUTPUT_FILE.exists():
        logger.info(f"File {OUTPUT_FILE} already exists. Verifying checksum...")
        if not verify_checksum(OUTPUT_FILE, expected_hash):
            logger.warning(f"Checksum mismatch for existing file. Re-downloading...")
            OUTPUT_FILE.unlink()
        else:
            logger.info(f"Checksum verified for existing file.")
            return {
                "status": "success",
                "action": "verified_existing",
                "file_path": str(OUTPUT_FILE),
                "checksum_verified": True
            }
    
    # Download the file
    logger.info(f"Downloading {REMOTE_FILENAME} from {DATASET_NAME}...")
    try:
        downloaded_path = download_dataset(DATASET_NAME, DATA_RAW_DIR, REMOTE_FILENAME)
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise
    
    # Verify checksum of downloaded file
    logger.info("Verifying downloaded file checksum...")
    if not verify_checksum(downloaded_path, expected_hash):
        computed = compute_sha256(downloaded_path)
        error_msg = (
            f"Checksum mismatch after download!\n"
            f"Expected: {expected_hash}\n"
            f"Computed: {computed}"
        )
        logger.error(error_msg)
        # Clean up the mismatched file
        downloaded_path.unlink()
        raise FileNotFoundError(error_msg)
    
    logger.info(f"Successfully ingested trajectories to {downloaded_path}")
    
    return {
        "status": "success",
        "action": "downloaded_and_verified",
        "file_path": str(downloaded_path),
        "checksum_verified": True,
        "file_size_bytes": downloaded_path.stat().st_size
    }


def main():
    """Entry point for T005b."""
    logger.info("Starting T005b: Ingest Real AgenticSTS Trajectories")
    try:
        result = run_ingestion()
        logger.info(f"T005b completed successfully: {result}")
        # Write a status artifact for downstream tasks
        status_path = DATA_RAW_DIR / "ingestion_status.json"
        with open(status_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        logger.info(f"Wrote status to {status_path}")
    except Exception as e:
        logger.critical(f"T005b failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
