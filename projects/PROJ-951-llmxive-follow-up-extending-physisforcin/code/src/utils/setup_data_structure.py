"""
Script to set up the data directory structure for the PhysisForcing project.
This script creates the required directories and initializes checksum tracking.
"""
import os
import sys
import logging
from pathlib import Path

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.io_utils import ensure_dirs, validate_project_structure, get_data_stats, update_checksums

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to set up the data structure."""
    logger.info("Starting data directory setup...")
    
    # Get the project root (parent of code/)
    code_dir = Path(__file__).parent.parent
    project_root = code_dir.parent
    os.chdir(project_root)
    logger.info(f"Project root: {project_root}")
    
    # Ensure data directories exist
    logger.info("Creating data directory structure...")
    ensure_dirs()
    
    # Validate the structure
    logger.info("Validating project structure...")
    is_valid, missing = validate_project_structure(project_root)
    
    if is_valid:
        logger.info("✓ All required directories created successfully.")
    else:
        logger.error(f"✗ Missing directories: {missing}")
        sys.exit(1)
    
    # Initialize checksums for the data directory
    data_path = project_root / "data"
    checksums_path = data_path / ".checksums.json"
    
    logger.info(f"Initializing checksums at {checksums_path}...")
    update_checksums(data_path, checksums_path)
    logger.info("✓ Checksums initialized.")
    
    # Display statistics
    logger.info("Data directory statistics:")
    stats = get_data_stats(project_root)
    logger.info(f"  Total size: {stats['total_size_bytes']:,} bytes")
    logger.info(f"  Total files: {stats['file_count']}")
    logger.info(f"  Total directories: {stats['directory_count']}")
    
    for subdir, subdir_stats in stats["by_subdirectory"].items():
        logger.info(f"  {subdir}: {subdir_stats['file_count']} files, {subdir_stats['size_bytes']:,} bytes")
    
    logger.info("Data directory setup completed successfully.")

if __name__ == "__main__":
    main()