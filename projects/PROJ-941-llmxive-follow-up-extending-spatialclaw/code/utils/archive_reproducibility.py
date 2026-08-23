"""
Reproducibility Archive Module (T049).

Creates a compressed tarball of the experiment state to ensure
reproducibility for future review.

Artifacts included:
- data/raw/
- results/logs/
- results/analysis/
- requirements.txt
"""
import os
import sys
import tarfile
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Configure logger
logger = logging.getLogger(__name__)

def setup_logger(name: str) -> logging.Logger:
    """Setup a basic logger for the archive process."""
    log_handler = logging.StreamHandler(sys.stdout)
    log_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_handler.setFormatter(formatter)
    
    root_logger = logging.getLogger(name)
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(log_handler)
    return root_logger

def collect_paths_to_archive(base_dir: str) -> List[Path]:
    """
    Collect all paths that need to be included in the archive.
    
    Args:
        base_dir: The root directory of the project.
        
    Returns:
        List of Path objects to include in the tarball.
    """
    paths_to_archive = []
    base_path = Path(base_dir)
    
    # Define relative paths to include
    relative_paths = [
        "data/raw",
        "results/logs",
        "results/analysis",
        "requirements.txt"
    ]
    
    for rel_path in relative_paths:
        full_path = base_path / rel_path
        if full_path.exists():
            if full_path.is_file():
                paths_to_archive.append(full_path)
            elif full_path.is_dir():
                # Recursively add all files in the directory
                for file_path in full_path.rglob("*"):
                    if file_path.is_file():
                        paths_to_archive.append(file_path)
            else:
                logger.warning(f"Path exists but is not a file or directory: {full_path}")
        else:
            # Check if the directory is empty or missing, log warning but continue
            # Some directories might not exist if the pipeline hasn't reached that stage yet
            logger.warning(f"Path not found, skipping: {full_path}")
            
    return paths_to_archive

def create_archive(
    base_dir: str,
    output_dir: str,
    timestamp: str,
    paths_to_archive: List[Path]
) -> str:
    """
    Create a compressed tarball of the specified paths.
    
    Args:
        base_dir: The project root directory.
        output_dir: The directory where the archive will be saved.
        timestamp: The timestamp string for the filename.
        paths_to_archive: List of paths to include.
        
    Returns:
        The path to the created archive.
    """
    base_path = Path(base_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    archive_name = f"spatialclaw_restriction_run_{timestamp}.tar.gz"
    archive_path = output_path / archive_name
    
    logger.info(f"Creating archive: {archive_path}")
    
    with tarfile.open(archive_path, "w:gz") as tar:
        for file_path in paths_to_archive:
            # Calculate the relative path from base_dir to preserve structure
            try:
                arc_name = file_path.relative_to(base_path)
            except ValueError:
                # Fallback if file is not relative to base_dir (shouldn't happen with our logic)
                arc_name = file_path.name
            
            logger.debug(f"Adding {file_path} -> {arc_name}")
            tar.add(file_path, arcname=arc_name)
    
    logger.info(f"Archive created successfully: {archive_path}")
    return str(archive_path)

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Create reproducibility archive for SpatialClaw experiment.")
    parser.add_argument(
        "--base-dir",
        type=str,
        default=".",
        help="Project root directory (default: current directory)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results/archive",
        help="Directory to store the archive (default: results/archive)"
    )
    parser.add_argument(
        "--timestamp",
        type=str,
        default=None,
        help="Custom timestamp string (default: current UTC timestamp)"
    )
    return parser.parse_args()

def main() -> None:
    """Main entry point for the archive script."""
    args = parse_args()
    logger = setup_logger("archive_reproducibility")
    
    base_dir = args.base_dir
    output_dir = args.output_dir
    
    if args.timestamp:
        timestamp = args.timestamp
    else:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    logger.info(f"Starting reproducibility archive generation...")
    logger.info(f"Base directory: {base_dir}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Timestamp: {timestamp}")
    
    # Collect paths
    paths_to_archive = collect_paths_to_archive(base_dir)
    
    if not paths_to_archive:
        logger.error("No files found to archive. Check if data/raw, results/logs, results/analysis, and requirements.txt exist.")
        sys.exit(1)
    
    logger.info(f"Found {len(paths_to_archive)} files to archive.")
    
    # Create archive
    archive_path = create_archive(base_dir, output_dir, timestamp, paths_to_archive)
    
    logger.info("Archive generation complete.")
    print(f"Archive created at: {archive_path}")

if __name__ == "__main__":
    main()
