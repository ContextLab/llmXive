import logging
import sys
import shutil
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

# Import from sibling modules as per API surface
from src.data.archive_utils import archive_data, generate_checksum_manifest
from src.config import setup_logging

def run_archive_pipeline(
    ebird_source: str = "data/raw/ebird_sample",
    climate_source: Optional[str] = None,
    archive_dest: str = "data/raw/archive",
    manifest_path: str = "data/provenance/archive_manifest.json",
    ci_upload_flag: bool = True
) -> Dict[str, Any]:
    """
    Archives raw data from eBird and the active climate source.
    Copies files to the archive directory, generates checksums,
    and prepares metadata for CI artifact upload.

    Args:
        ebird_source: Path to the downloaded eBird sample.
        climate_source: Path to the active climate data (noaa_prism or daymet).
        archive_dest: Destination directory for the archive.
        manifest_path: Path to write the JSON manifest.
        ci_upload_flag: If True, generates a CI-specific metadata file.

    Returns:
        A dictionary containing the archive status and manifest path.
    """
    logger = setup_logging("archive_pipeline")
    logger.info("Starting archive pipeline...")

    source_paths: List[Path] = []
    archive_path = Path(archive_dest)
    archive_path.mkdir(parents=True, exist_ok=True)

    # Validate and collect source paths
    ebird_path = Path(ebird_source)
    if not ebird_path.exists():
        raise FileNotFoundError(f"eBird source not found: {ebird_path}")
    source_paths.append(ebird_path)
    logger.info(f"Confirmed eBird source: {ebird_path}")

    if climate_source:
        climate_path = Path(climate_source)
        if not climate_path.exists():
            # Depending on strictness, we might fail here or warn.
            # Per task description, we archive the *active* source.
            # If T005c2 ran, this should exist. If T005c1 failed, it might not.
            # We raise to ensure we don't archive incomplete data without explicit handling.
            raise FileNotFoundError(f"Climate source not found: {climate_path}")
        source_paths.append(climate_path)
        logger.info(f"Confirmed climate source: {climate_path}")

    # Archive the data
    logger.info(f"Archiving data to {archive_path}...")
    for src in source_paths:
        # archive_data handles the copying logic
        archive_data(src, archive_path)

    # Generate checksums
    logger.info("Generating checksum manifest...")
    manifest = generate_checksum_manifest(archive_path)
    
    # Write manifest
    manifest_path_obj = Path(manifest_path)
    manifest_path_obj.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path_obj, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Manifest written to {manifest_path_obj}")

    # Prepare CI Upload Metadata
    if ci_upload_flag:
        ci_meta = {
            "archive_path": str(archive_path),
            "manifest_path": str(manifest_path_obj),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sources_archived": [str(p) for p in source_paths],
            "total_files": manifest.get("total_files", 0),
            "total_size_bytes": manifest.get("total_size_bytes", 0),
            "ci_action": "upload_artifact",
            "artifact_name": "raw_data_provenance"
        }
        ci_meta_path = archive_path / "ci_upload_metadata.json"
        with open(ci_meta_path, 'w', encoding='utf-8') as f:
            json.dump(ci_meta, f, indent=2)
        logger.info(f"CI metadata prepared at {ci_meta_path}")

    logger.info("Archive pipeline completed successfully.")
    return {
        "status": "success",
        "archive_path": str(archive_path),
        "manifest_path": str(manifest_path_obj),
        "ci_metadata_path": str(ci_meta_path) if ci_upload_flag else None
    }

def main():
    """Entry point for the archive pipeline script."""
    import argparse
    parser = argparse.ArgumentParser(description="Archive raw data for CI provenance.")
    parser.add_argument("--ebird-source", default="data/raw/ebird_sample", help="Path to eBird data")
    parser.add_argument("--climate-source", default=None, help="Path to climate data (noaa_prism or daymet)")
    parser.add_argument("--archive-dest", default="data/raw/archive", help="Destination archive path")
    parser.add_argument("--manifest", default="data/provenance/archive_manifest.json", help="Manifest output path")
    
    args = parser.parse_args()

    try:
        result = run_archive_pipeline(
            ebird_source=args.ebird_source,
            climate_source=args.climate_source,
            archive_dest=args.archive_dest,
            manifest_path=args.manifest
        )
        print(f"Archive completed: {result['archive_path']}")
        print(f"Manifest: {result['manifest_path']}")
        if result['ci_metadata_path']:
            print(f"CI Metadata: {result['ci_metadata_path']}")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Archive pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
