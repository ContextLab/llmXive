import logging
import sys
import hashlib
import shutil
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

from src.data.archive_utils import archive_data, generate_checksum_manifest
from src.config import setup_logging

logger = logging.getLogger(__name__)

def load_source_paths() -> List[Path]:
    """
    Defines the source paths that need to be archived.
    Based on T005b (eBird) and T005c2 (Daymet) outputs.
    """
    base = Path("data/raw")
    paths = []
    
    # Check for eBird sample data artifacts (from T005b)
    ebird_candidates = [
        base / "ebird_sample.parquet",
        base / "ebird_sample", # Directory if extracted
        base / "vvud_eb_data"
    ]
    for p in ebird_candidates:
        if p.exists():
            paths.append(p)
            break

    # Check for Daymet climate data artifacts (from T005c2)
    daymet_candidates = [
        base / "daymet_climate.parquet",
        base / "daymet_climate",
        base / "daymet_annual"
    ]
    for p in daymet_candidates:
        if p.exists():
            paths.append(p)
            break

    if not paths:
        logger.warning("No source data files found in data/raw for archiving.")
        return []
    
    return paths

def run_archive_pipeline(output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Orchestrates the archiving of downloaded raw data files.
    
    1. Identifies source files in data/raw.
    2. Copies them unchanged to data/raw/archive/.
    3. Computes SHA-256 checksums for each archived file.
    4. Writes a manifest JSON file.
    
    Args:
        output_dir: Optional override for the archive destination. Defaults to data/raw/archive.
        
    Returns:
        Dictionary containing the archive path and the manifest data.
    """
    if output_dir is None:
        output_dir = Path("data/raw/archive")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    source_paths = load_source_paths()
    
    if not source_paths:
        logger.error("No source files found to archive. Aborting.")
        raise FileNotFoundError("No source data files found in data/raw to archive.")
    
    manifest_data = {
        "archive_root": str(output_dir),
        "timestamp": None, # Set by archive_utils or here if needed
        "files": []
    }
    
    for src_path in source_paths:
        logger.info(f"Archiving: {src_path}")
        
        # Determine destination name (preserve relative structure or just filename)
        if src_path.is_file():
            dest_name = src_path.name
        else:
            dest_name = src_path.name
        
        dest_path = output_dir / dest_name
        
        # Perform the archive copy
        archive_result = archive_data(src_path, dest_path)
        
        if archive_result["success"]:
            manifest_data["files"].append({
                "original_path": str(src_path),
                "archived_path": str(dest_path),
                "sha256": archive_result["checksum"],
                "size_bytes": archive_result["size"],
                "is_directory": src_path.is_dir()
            })
            logger.info(f"Archived and checksummed: {dest_path} ({archive_result['checksum'][:16]}...)")
        else:
            logger.error(f"Failed to archive {src_path}: {archive_result.get('error', 'Unknown error')}")
            raise RuntimeError(f"Archive failed for {src_path}")
    
    # Generate and save the manifest
    manifest_path = output_dir / "checksum_manifest.json"
    generate_checksum_manifest(manifest_data, manifest_path)
    
    logger.info(f"Archive complete. Manifest written to {manifest_path}")
    
    return {
        "archive_root": str(output_dir),
        "manifest_path": str(manifest_path),
        "files_archived": len(manifest_data["files"])
    }

def main():
    """Entry point for running the archive pipeline."""
    setup_logging()
    try:
        result = run_archive_pipeline()
        print(f"Pipeline completed successfully. {result['files_archived']} items archived.")
        print(f"Manifest: {result['manifest_path']}")
    except Exception as e:
        logger.exception("Pipeline failed")
        print(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
