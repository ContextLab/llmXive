"""
Task T012f: Record computed SHA-256 checksum in data/raw/checksums.json.

This script locates the ADReSS dataset archive (downloaded by T012),
computes its SHA-256 hash, and records the result in data/raw/checksums.json.
It depends on T012 having successfully downloaded the dataset.
"""
import json
import logging
import sys
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional

from config import get_path, ensure_dirs


def load_existing_checksums(checksum_path: Path) -> Dict[str, Any]:
    """Load existing checksums file if it exists, otherwise return empty dict."""
    if checksum_path.exists():
        try:
            with open(checksum_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logging.warning(f"Could not read existing checksums file: {e}. Starting fresh.")
    return {"checksums": []}


def save_checksums(checksum_path: Path, data: Dict[str, Any]) -> None:
    """Save the checksums data to the specified JSON file."""
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    with open(checksum_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    logging.info(f"Checksums saved to {checksum_path}")


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def find_dataset_archive(raw_dir: Path) -> Optional[Path]:
    """
    Find the ADReSS dataset archive in the raw directory.
    Looks for common archive extensions (.zip, .tar.gz, .tgz).
    """
    extensions = ['.zip', '.tar.gz', '.tgz', '.tar']
    candidates = []
    for ext in extensions:
        matches = list(raw_dir.glob(f"*{ext}"))
        candidates.extend(matches)
    
    if not candidates:
        # Fallback: look for any file if no extension matches
        candidates = [f for f in raw_dir.iterdir() if f.is_file()]
    
    if not candidates:
        return None
    
    # Prefer the largest file (likely the dataset) or the first match
    # ADReSS is typically a single zip file
    return max(candidates, key=lambda p: p.stat().st_size)


def main() -> int:
    """Main entry point for T012f."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    # Define paths
    raw_dir = get_path("data_raw")
    checksum_path = get_path("data_raw_checksums")
    
    ensure_dirs([raw_dir, checksum_path.parent])

    # Find the dataset archive
    dataset_file = find_dataset_archive(raw_dir)
    
    if not dataset_file:
        logger.error("No dataset archive found in data/raw/. "
                     "Ensure T012 (download) has completed successfully.")
        return 1

    logger.info(f"Found dataset archive: {dataset_file.name}")

    # Compute hash
    file_hash = compute_sha256(dataset_file)
    logger.info(f"Computed SHA-256 for {dataset_file.name}: {file_hash}")

    # Load existing data (to preserve other entries if any)
    checksum_data = load_existing_checksums(checksum_path)

    # Update or add entry
    # Check if file already exists in list to avoid duplicates
    existing_files = {item.get('filename') for item in checksum_data.get('checksums', [])}
    
    if dataset_file.name in existing_files:
        logger.info(f"Updating checksum for existing file: {dataset_file.name}")
        checksum_data['checksums'] = [
            item if item.get('filename') != dataset_file.name 
            else {"filename": dataset_file.name, "sha256": file_hash}
            for item in checksum_data['checksums']
        ]
    else:
        logger.info(f"Adding new checksum entry for: {dataset_file.name}")
        checksum_data['checksums'].append({
            "filename": dataset_file.name,
            "sha256": file_hash
        })

    # Save updated checksums
    save_checksums(checksum_path, checksum_data)

    logger.info("Task T012f completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())