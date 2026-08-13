import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from src.utils.logging import get_logger

logger = get_logger(__name__)

def compute_file_checksum(file_path: str) -> Optional[str]:
    """Compute SHA256 checksum of a file."""
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

def check_fetch_status(raw_data_dir: str) -> Dict[str, bool]:
    """Check if raw data files exist for arXiv and PubMed."""
    raw_path = Path(raw_data_dir)
    if not raw_path.exists():
        logger.warning(f"Raw data directory does not exist: {raw_data_dir}")
        return {"arxiv_fetch_status": False, "pubmed_fetch_status": False}

    arxiv_exists = any(raw_path.glob("arxiv_*.jsonl"))
    pubmed_exists = any(raw_path.glob("pubmed_*.jsonl"))

    logger.info(f"ArXiv fetch status: {arxiv_exists}")
    logger.info(f"PubMed fetch status: {pubmed_exists}")

    return {
        "arxiv_fetch_status": arxiv_exists,
        "pubmed_fetch_status": pubmed_exists
    }

def gather_processed_checksums(processed_data_dir: str) -> Dict[str, str]:
    """Gather checksums for all processed CSV files."""
    processed_path = Path(processed_data_dir)
    checksums = {}

    if not processed_path.exists():
        logger.warning(f"Processed data directory does not exist: {processed_data_dir}")
        return checksums

    for file_path in processed_path.glob("*.csv"):
        checksum = compute_file_checksum(str(file_path))
        if checksum:
            # Store relative path as key
            rel_key = str(file_path.relative_to(processed_path))
            checksums[rel_key] = checksum

    logger.info(f"Gathered {len(checksums)} processed file checksums")
    return checksums

def update_manifest(manifest_path: str, arxiv_status: bool, pubmed_status: bool, 
                   processed_checksums: Dict[str, str], raw_checksums: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Update or create the manifest.json with fetch status and checksums."""
    manifest_dir = Path(manifest_path).parent
    manifest_dir.mkdir(parents=True, exist_ok=True)

    # Load existing manifest if it exists
    if Path(manifest_path).exists():
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            logger.info("Loaded existing manifest")
        except Exception as e:
            logger.warning(f"Could not load existing manifest, creating new: {e}")
            manifest = {"created_at": datetime.now(timezone.utc).isoformat()}
    else:
        manifest = {"created_at": datetime.now(timezone.utc).isoformat()}
        logger.info("Created new manifest")

    # Update with fetch status
    manifest["arxiv_fetch_status"] = arxiv_status
    manifest["pubmed_fetch_status"] = pubmed_status

    # Update with checksums
    manifest["processed_data_checksums"] = processed_checksums
    if raw_checksums:
        manifest["raw_data_checksums"] = raw_checksums

    # Update timestamp
    manifest["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Save manifest
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Manifest updated successfully at {manifest_path}")
    return manifest

def main():
    """Main entry point for updating the manifest."""
    # Define paths based on project structure
    project_root = Path(__file__).parent.parent.parent.parent
    raw_data_dir = project_root / "data" / "raw"
    processed_data_dir = project_root / "data" / "processed"
    manifest_path = project_root / "results" / "manifest.json"

    logger.info("Starting manifest update process")

    # Check fetch status
    fetch_status = check_fetch_status(str(raw_data_dir))
    
    # Gather processed checksums
    processed_checksums = gather_processed_checksums(str(processed_data_dir))
    
    # Gather raw checksums (optional)
    raw_checksums = {}
    for file_path in list(raw_data_dir.glob("*.jsonl")) if raw_data_dir.exists() else []:
        checksum = compute_file_checksum(str(file_path))
        if checksum:
            raw_checksums[str(file_path.relative_to(raw_data_dir))] = checksum

    # Update manifest
    manifest = update_manifest(
        str(manifest_path),
        fetch_status["arxiv_fetch_status"],
        fetch_status["pubmed_fetch_status"],
        processed_checksums,
        raw_checksums if raw_checksums else None
    )

    logger.info(f"Final manifest status: ArXiv={manifest['arxiv_fetch_status']}, PubMed={manifest['pubmed_fetch_status']}")
    return 0

if __name__ == "__main__":
    import sys
    from datetime import datetime, timezone
    sys.exit(main())
