import logging
import sys
from pathlib import Path
from typing import Optional
from src.data.archive_utils import archive_data, generate_checksum_manifest
from src.config import setup_logging

logger = logging.getLogger(__name__)

def run_archive_pipeline(
    source_dir: Path,
    archive_dir: Path,
    manifest_path: Optional[Path] = None
) -> dict:
    """
    Execute the archive pipeline: copy files to archive and generate checksums.
    
    Args:
        source_dir: Path to the source directory containing raw data.
        archive_dir: Path to the destination archive directory.
        manifest_path: Optional path for the checksum manifest file.
        
    Returns:
        Dictionary containing pipeline execution results.
    """
    logger.info(f"Starting archive pipeline: {source_dir} -> {archive_dir}")
    
    if not source_dir.exists():
        raise FileNotFoundError(f"Source directory not found: {source_dir}")
    
    archive_data(source_dir, archive_dir, overwrite=True)
    
    result = {
        "source": str(source_dir),
        "archive": str(archive_dir),
        "status": "success"
    }
    
    if manifest_path:
        checksums = generate_checksum_manifest(archive_dir, manifest_path)
        result["manifest"] = str(manifest_path)
        result["checksum_count"] = len(checksums)
        logger.info(f"Generated checksum manifest: {manifest_path} ({len(checksums)} files)")
    
    logger.info("Archive pipeline completed successfully.")
    return result

def main():
    """
    Main entry point for the archive pipeline script.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Archive raw data and generate checksums.")
    parser.add_argument("--source", type=str, required=True, help="Source directory path")
    parser.add_argument("--archive", type=str, required=True, help="Archive directory path")
    parser.add_argument("--manifest", type=str, help="Output manifest file path (optional)")
    args = parser.parse_args()
    
    setup_logging()
    
    source_dir = Path(args.source)
    archive_dir = Path(args.archive)
    manifest_path = Path(args.manifest) if args.manifest else None
    
    try:
        result = run_archive_pipeline(source_dir, archive_dir, manifest_path)
        print(f"Pipeline Result: {result}")
        return 0
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())