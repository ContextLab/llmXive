import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from src.utils.logging import get_logger

logger = get_logger(__name__)

def compute_file_checksum(file_path: str) -> Optional[str]:
    """
    Compute SHA256 checksum of a file.
    Returns None if file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"File not found for checksum: {file_path}")
        return None

    sha256_hash = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error computing checksum for {file_path}: {e}")
        return None

def check_fetch_status(raw_dir: Path) -> Dict[str, str]:
    """
    Check the status of arXiv and PubMed fetches by looking for raw JSONL files.
    Returns a dict with 'arxiv_fetch_status' and 'pubmed_fetch_status'.
    """
    status = {
        "arxiv_fetch_status": "not_found",
        "pubmed_fetch_status": "not_found"
    }

    arxiv_files = list(raw_dir.glob("*arxiv*.jsonl"))
    if arxiv_files:
        # Check if file is non-empty
        for f in arxiv_files:
            if f.stat().st_size > 0:
                status["arxiv_fetch_status"] = "success"
                break
        else:
            status["arxiv_fetch_status"] = "empty"

    pubmed_files = list(raw_dir.glob("*pubmed*.jsonl"))
    if pubmed_files:
        for f in pubmed_files:
            if f.stat().st_size > 0:
                status["pubmed_fetch_status"] = "success"
                break
        else:
            status["pubmed_fetch_status"] = "empty"

    return status

def gather_processed_checksums(processed_dir: Path) -> Dict[str, str]:
    """
    Gather checksums for all processed CSV files partitioned by window.
    Returns a dict mapping filename to checksum.
    """
    checksums = {}
    if not processed_dir.exists():
        logger.warning(f"Processed directory does not exist: {processed_dir}")
        return checksums

    csv_files = list(processed_dir.glob("*.csv"))
    for f in csv_files:
        checksum = compute_file_checksum(str(f))
        if checksum:
            checksums[f.name] = checksum

    return checksums

def update_manifest(
    manifest_path: Path,
    raw_dir: Path,
    processed_dir: Path,
    additional_data: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Update the results/manifest.json with fetch statuses and data checksums.
    Creates the manifest if it doesn't exist.
    Returns True on success, False on failure.
    """
    # Ensure directories exist
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Load existing manifest or create new one
    if manifest_path.exists():
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load existing manifest: {e}")
            manifest = {}
    else:
        manifest = {}

    # Check fetch status
    fetch_status = check_fetch_status(raw_dir)
    manifest["arxiv_fetch_status"] = fetch_status["arxiv_fetch_status"]
    manifest["pubmed_fetch_status"] = fetch_status["pubmed_fetch_status"]

    # Gather processed data checksums
    processed_checksums = gather_processed_checksums(processed_dir)
    manifest["data_checksums"] = processed_checksums

    # Add any additional data
    if additional_data:
        manifest.update(additional_data)

    # Save updated manifest
    try:
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Manifest updated successfully at {manifest_path}")
        return True
    except IOError as e:
        logger.error(f"Failed to save manifest: {e}")
        return False

def main():
    """
    Main entry point for updating the manifest.
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    manifest_path = project_root / "results" / "manifest.json"

    logger.info(f"Updating manifest at {manifest_path}")
    logger.info(f"Raw data directory: {raw_dir}")
    logger.info(f"Processed data directory: {processed_dir}")

    success = update_manifest(manifest_path, raw_dir, processed_dir)

    if success:
        logger.info("Manifest update completed successfully.")
        # Print summary
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        print(f"arXiv fetch status: {manifest.get('arxiv_fetch_status', 'unknown')}")
        print(f"PubMed fetch status: {manifest.get('pubmed_fetch_status', 'unknown')}")
        print(f"Processed files checksums: {len(manifest.get('data_checksums', {}))} files")
    else:
        logger.error("Manifest update failed.")
        exit(1)

if __name__ == "__main__":
    main()