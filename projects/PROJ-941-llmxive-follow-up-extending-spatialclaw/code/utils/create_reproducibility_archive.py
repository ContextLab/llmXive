"""
T049: Reproducibility Archive Implementation.

Creates a compressed tarball of the entire experiment state including:
- data/raw/ (generated datasets)
- results/logs/ (execution logs)
- results/analysis/ (statistical reports, CSVs)
- requirements.txt (exact dependencies)

Naming: spatialclaw_restriction_run_<timestamp>.tar.gz
"""
import os
import sys
import tarfile
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Configure logging
logger = logging.getLogger(__name__)

def setup_logger() -> logging.Logger:
    """Setup logger for archive creation."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

def collect_paths_to_archive(project_root: str) -> List[Path]:
    """
    Collect all paths that need to be included in the archive.
    
    Returns a list of Path objects relative to project_root.
    """
    paths = []
    
    # Directories to archive
    dirs_to_archive = [
        "data/raw",
        "results/logs",
        "results/analysis",
    ]
    
    # Files to archive
    files_to_archive = [
        "requirements.txt",
    ]
    
    root_path = Path(project_root)
    
    for dir_path in dirs_to_archive:
        full_path = root_path / dir_path
        if full_path.exists() and full_path.is_dir():
            # Collect all files in the directory
            for file_path in full_path.rglob("*"):
                if file_path.is_file():
                    paths.append(file_path)
                    logger.info(f"Found: {file_path.relative_to(root_path)}")
        else:
            logger.warning(f"Directory not found, skipping: {dir_path}")
    
    for file_path in files_to_archive:
        full_path = root_path / file_path
        if full_path.exists():
            paths.append(full_path)
            logger.info(f"Found: {file_path}")
        else:
            logger.warning(f"File not found, skipping: {file_path}")
    
    return paths

def create_archive(
    project_root: str,
    output_dir: str,
    timestamp: Optional[str] = None
) -> str:
    """
    Create a compressed tarball of the experiment state.
    
    Args:
        project_root: Root directory of the project
        output_dir: Directory where the archive will be saved
        timestamp: Optional timestamp string (defaults to current time)
    
    Returns:
        Path to the created archive file
    """
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    archive_name = f"spatialclaw_restriction_run_{timestamp}.tar.gz"
    archive_path = Path(output_dir) / archive_name
    
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Collect paths to archive
    paths_to_archive = collect_paths_to_archive(project_root)
    
    if not paths_to_archive:
        raise FileNotFoundError(
            "No files found to archive. Ensure data/raw/, results/logs/, "
            "results/analysis/, and requirements.txt exist."
        )
    
    logger.info(f"Creating archive: {archive_path}")
    logger.info(f"Total files to archive: {len(paths_to_archive)}")
    
    # Create the tarball
    with tarfile.open(archive_path, "w:gz") as tar:
        for file_path in paths_to_archive:
            # Calculate relative path for the archive
            relative_path = file_path.relative_to(Path(project_root))
            
            # Add to archive with the relative path
            tar.add(file_path, arcname=relative_path)
            logger.debug(f"Added to archive: {relative_path}")
    
    # Verify archive size
    archive_size_mb = archive_path.stat().st_size / (1024 * 1024)
    logger.info(f"Archive created successfully: {archive_path}")
    logger.info(f"Archive size: {archive_size_mb:.2f} MB")
    
    return str(archive_path)

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Create reproducibility archive for SpatialClaw experiment."
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=".",
        help="Project root directory (default: current directory)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results/archive",
        help="Output directory for the archive (default: results/archive)"
    )
    parser.add_argument(
        "--timestamp",
        type=str,
        default=None,
        help="Custom timestamp for archive name (default: current time)"
    )
    return parser.parse_args()

def main() -> int:
    """
    Main entry point for the reproducibility archive script.
    
    Returns:
        0 on success, 1 on failure
    """
    args = parse_args()
    setup_logger()
    
    try:
        project_root = os.path.abspath(args.project_root)
        output_dir = os.path.abspath(args.output_dir)
        
        logger.info(f"Project root: {project_root}")
        logger.info(f"Output directory: {output_dir}")
        
        archive_path = create_archive(
            project_root=project_root,
            output_dir=output_dir,
            timestamp=args.timestamp
        )
        
        logger.info(f"SUCCESS: Archive created at {archive_path}")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"FILE NOT FOUND: {e}")
        return 1
    except Exception as e:
        logger.error(f"ERROR: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())