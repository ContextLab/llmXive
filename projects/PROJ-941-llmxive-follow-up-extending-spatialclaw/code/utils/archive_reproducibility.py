"""
Reproducibility Archive Generator (T049).

Creates a compressed tarball of the experiment state for future review.
Includes data/raw/, results/logs/, results/analysis/, and requirements.txt.
"""
import os
import sys
import tarfile
import logging
import argparse
from datetime import datetime
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_logger() -> logging.Logger:
    """Return the configured logger."""
    return logger

def collect_paths_to_archive(root_dir: str) -> List[str]:
    """
    Collect all paths relative to root_dir that should be included in the archive.
    
    Args:
        root_dir: The project root directory.
        
    Returns:
        List of absolute paths to include.
    """
    paths_to_archive = []
    
    # Define relative paths to include
    relative_paths = [
        'data/raw/',
        'results/logs/',
        'results/analysis/',
        'requirements.txt'
    ]
    
    for rel_path in relative_paths:
        abs_path = os.path.join(root_dir, rel_path)
        if os.path.exists(abs_path):
            if os.path.isfile(abs_path):
                paths_to_archive.append(abs_path)
            elif os.path.isdir(abs_path):
                # Walk directory to get all files
                for dirpath, dirnames, filenames in os.walk(abs_path):
                    for filename in filenames:
                        full_path = os.path.join(dirpath, filename)
                        paths_to_archive.append(full_path)
            else:
                logger.warning(f"Path exists but is neither file nor dir: {abs_path}")
        else:
            logger.warning(f"Path does not exist, skipping: {abs_path}")
    
    return paths_to_archive

def create_archive(
    root_dir: str,
    output_path: str,
    files_to_archive: List[str]
) -> str:
    """
    Create a compressed tarball containing the specified files.
    
    Args:
        root_dir: The project root directory (used for relative paths in archive).
        output_path: Full path where the archive will be written.
        files_to_archive: List of absolute paths to include.
        
    Returns:
        The path to the created archive.
    """
    logger.info(f"Creating archive at: {output_path}")
    
    with tarfile.open(output_path, "w:gz") as tar:
        for abs_path in files_to_archive:
            # Calculate relative path for archive structure
            try:
                arcname = os.path.relpath(abs_path, root_dir)
            except ValueError:
                # Handle case where paths are on different drives (Windows)
                arcname = os.path.basename(abs_path)
                
            logger.debug(f"Adding to archive: {arcname}")
            tar.add(abs_path, arcname=arcname)
    
    logger.info(f"Archive created successfully: {output_path}")
    return output_path

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Create reproducibility archive for the SpatialClaw experiment."
    )
    parser.add_argument(
        "--root-dir",
        type=str,
        default=".",
        help="Project root directory (default: current directory)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results/archive",
        help="Directory to write the archive (default: results/archive)"
    )
    parser.add_argument(
        "--timestamp",
        type=str,
        default=None,
        help="Custom timestamp for archive name (default: current timestamp)"
    )
    return parser.parse_args()

def main() -> int:
    """
    Main entry point for the archive script.
    
    Returns:
        0 on success, 1 on failure.
    """
    args = parse_args()
    
    # Resolve root directory
    root_dir = os.path.abspath(args.root_dir)
    if not os.path.isdir(root_dir):
        logger.error(f"Root directory does not exist: {root_dir}")
        return 1
    
    # Prepare output directory
    output_dir = os.path.abspath(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate archive name
    if args.timestamp:
        timestamp_str = args.timestamp
    else:
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    archive_name = f"spatialclaw_restriction_run_{timestamp_str}.tar.gz"
    archive_path = os.path.join(output_dir, archive_name)
    
    # Check if archive already exists
    if os.path.exists(archive_path):
        logger.warning(f"Archive already exists: {archive_path}")
        # Optional: Could add --overwrite flag if needed
        # For now, we proceed and overwrite
    
    # Collect files to archive
    logger.info(f"Scanning for files in: {root_dir}")
    files_to_archive = collect_paths_to_archive(root_dir)
    
    if not files_to_archive:
        logger.error("No files found to archive. Check that data/raw/, results/logs/, "
                    "results/analysis/, and requirements.txt exist.")
        return 1
    
    logger.info(f"Found {len(files_to_archive)} files to archive.")
    
    # Create archive
    try:
        create_archive(root_dir, archive_path, files_to_archive)
        logger.info(f"Reproducibility archive created successfully: {archive_path}")
        return 0
    except Exception as e:
        logger.error(f"Failed to create archive: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())