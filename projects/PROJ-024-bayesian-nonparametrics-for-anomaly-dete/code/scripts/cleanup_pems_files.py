"""
Script to delete PEMS-SF files from data/raw/ directory.

This script implements task T054: Delete all PEMS-SF files 
(pems_sf.csv, pems_sf_synthetic.csv) from data/raw/.
"""
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def cleanup_pems_files():
    """
    Delete PEMS-SF files from data/raw/ directory.
    
    Returns:
        bool: True if all files were successfully deleted or didn't exist,
              False if any deletion failed.
    """
    # Get project root (assuming script is at code/scripts/)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    data_raw_dir = project_root / 'data' / 'raw'
    
    # Files to delete
    pems_files = [
        'pems_sf.csv',
        'pems_sf_synthetic.csv'
    ]
    
    success = True
    
    for filename in pems_files:
        file_path = data_raw_dir / filename
        
        if not file_path.exists():
            logger.info(f"File does not exist, skipping: {file_path}")
            continue
        
        try:
            file_size = file_path.stat().st_size
            file_path.unlink()
            logger.info(f"Successfully deleted: {file_path} (size: {file_size} bytes)")
        except Exception as e:
            logger.error(f"Failed to delete {file_path}: {e}")
            success = False
    
    # Verify deletion
    remaining_files = [f for f in pems_files if (data_raw_dir / f).exists()]
    
    if remaining_files:
        logger.error(f"Files still exist after cleanup: {remaining_files}")
        success = False
    else:
        logger.info("Verification complete: No PEMS-SF files found in data/raw/")
    
    return success

def main():
    """Main entry point for the script."""
    logger.info("=" * 60)
    logger.info("PEMS-SF File Cleanup Script")
    logger.info("=" * 60)
    
    success = cleanup_pems_files()
    
    if success:
        logger.info("=" * 60)
        logger.info("Cleanup completed successfully")
        logger.info("=" * 60)
        sys.exit(0)
    else:
        logger.error("=" * 60)
        logger.error("Cleanup completed with errors")
        logger.error("=" * 60)
        sys.exit(1)

if __name__ == '__main__':
    main()
