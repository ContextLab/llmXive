import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional

from src.utils.logging import get_logger

logger = get_logger(__name__)

def compute_file_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def check_fetch_status(fetcher_name: str, raw_dir: Path) -> Dict[str, Any]:
    """
    Check the status of a fetcher by looking for raw JSONL files.
    Returns a dict with 'status' ('success', 'partial', 'failed') and 'count'.
    """
    pattern = f"*{fetcher_name}*.jsonl"
    files = list(raw_dir.glob(pattern))
    
    if not files:
        return {"status": "failed", "count": 0, "files": []}
    
    total_records = 0
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as fh:
                # Count lines (assuming one JSON object per line)
                count = sum(1 for _ in fh)
                total_records += count
        except Exception as e:
            logger.warning(f"Could not read {f}: {e}")
    
    status = "success" if total_records > 0 else "failed"
    return {
        "status": status,
        "count": total_records,
        "files": [str(f.relative_to(raw_dir)) for f in files]
    }

def gather_processed_checksums(processed_dir: Path) -> Dict[str, str]:
    """
    Gather checksums for all processed CSV files in the directory.
    Returns a dict mapping filename to checksum.
    """
    checksums = {}
    if not processed_dir.exists():
        logger.warning(f"Processed directory {processed_dir} does not exist.")
        return checksums
    
    for file_path in processed_dir.glob("*.csv"):
        checksum = compute_file_checksum(file_path)
        checksums[str(file_path.relative_to(processed_dir))] = checksum
    
    return checksums

def update_manifest(
    manifest_path: Path,
    arxiv_status: Dict[str, Any],
    pubmed_status: Dict[str, Any],
    processed_checksums: Dict[str, str],
    raw_dir: Path,
    processed_dir: Path
) -> None:
    """
    Update or create the results/manifest.json with fetch statuses and checksums.
    """
    # Load existing manifest if it exists
    if manifest_path.exists():
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
    else:
        manifest = {
            "pipeline_version": "1.0.0",
            "generated_at": None,
            "data": {}
        }
    
    # Ensure data section exists
    if "data" not in manifest:
        manifest["data"] = {}
    
    # Update fetch statuses
    manifest["data"]["arxiv_fetch_status"] = arxiv_status
    manifest["data"]["pubmed_fetch_status"] = pubmed_status
    
    # Update processed file checksums
    manifest["data"]["processed_file_checksums"] = processed_checksums
    
    # Update raw file checksums (optional but good for reproducibility)
    raw_checksums = {}
    if raw_dir.exists():
        for f in raw_dir.glob("*.jsonl"):
            raw_checksums[str(f.relative_to(raw_dir))] = compute_file_checksum(f)
    manifest["data"]["raw_file_checksums"] = raw_checksums
    
    # Ensure directory exists
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save manifest
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Manifest updated at {manifest_path}")

def main() -> None:
    """Main entry point for the manifest updater script."""
    # Define paths relative to project root (assuming code/ is root for this script execution context)
    # Adjust based on actual project structure if needed
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    results_dir = project_root / "results"
    data_raw_dir = project_root / "data" / "raw"
    data_processed_dir = project_root / "data" / "processed"
    manifest_path = results_dir / "manifest.json"
    
    logger.info("Starting manifest update...")
    
    # Check fetch statuses
    arxiv_status = check_fetch_status("arxiv", data_raw_dir)
    pubmed_status = check_fetch_status("pubmed", data_raw_dir)
    
    logger.info(f"ArXiv fetch status: {arxiv_status}")
    logger.info(f"PubMed fetch status: {pubmed_status}")
    
    # Gather processed checksums
    processed_checksums = gather_processed_checksums(data_processed_dir)
    logger.info(f"Found {len(processed_checksums)} processed files with checksums.")
    
    # Update manifest
    update_manifest(
        manifest_path,
        arxiv_status,
        pubmed_status,
        processed_checksums,
        data_raw_dir,
        data_processed_dir
    )
    
    logger.info("Manifest update completed.")

if __name__ == "__main__":
    main()
