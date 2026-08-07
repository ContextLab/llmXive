import logging
import sys
from pathlib import Path
from typing import Optional

from src.data.archive_utils import archive_data, generate_checksum_manifest
from src.config import setup_logging

logger = logging.getLogger(__name__)

def run_archive_pipeline(
    source_dir: Path,
    archive_dir: Optional[Path] = None,
    manifest_path: Optional[Path] = None
) -> dict:
    """
    Run the archiving pipeline: copy files to archive and generate checksums.
    
    Args:
        source_dir: Directory containing the downloaded raw data files.
        archive_dir: Directory where files will be archived. Defaults to source_dir/../archive.
        manifest_path: Path for the checksum manifest. Defaults to archive_dir/checksums.json.
        
    Returns:
        Dictionary containing archive status and checksums.
    """
    # Set up default paths if not provided
    if archive_dir is None:
        archive_dir = source_dir.parent / "archive"
    
    if manifest_path is None:
        manifest_path = archive_dir / "checksums.json"
    
    logger.info(f"Starting archive pipeline")
    logger.info(f"  Source: {source_dir}")
    logger.info(f"  Archive: {archive_dir}")
    logger.info(f"  Manifest: {manifest_path}")
    
    # Archive the data
    checksums = archive_data(source_dir, archive_dir, overwrite=False)
    
    if not checksums:
        logger.warning("No files were archived. Source directory may be empty.")
        return {
            "status": "warning",
            "message": "No files archived",
            "checksums": {}
        }
    
    # Generate manifest
    generate_checksum_manifest(checksums, manifest_path)
    
    logger.info("Archive pipeline completed successfully")
    return {
        "status": "success",
        "files_archived": len(checksums),
        "archive_dir": str(archive_dir),
        "manifest_path": str(manifest_path),
        "checksums": checksums
    }

def main():
    """Main entry point for the archive pipeline script."""
    setup_logging()
    
    # Default paths based on project structure
    source_dir = Path("data/raw")
    archive_dir = Path("data/raw/archive")
    manifest_path = Path("data/raw/archive/checksums.json")
    
    try:
        result = run_archive_pipeline(source_dir, archive_dir, manifest_path)
        
        if result["status"] == "success":
            logger.info(f"Successfully archived {result['files_archived']} files")
            logger.info(f"Checksums saved to {result['manifest_path']}")
            return 0
        else:
            logger.warning(result["message"])
            return 1
            
    except Exception as e:
        logger.error(f"Archive pipeline failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())