"""
T049: Reproducibility Archive Generator.
Creates a compressed tarball of all experimental artifacts and the requirements file.
"""
import os
import sys
import tarfile
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Project root detection (assumes running from root or code/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Directories to archive relative to PROJECT_ROOT
ARCHIVE_PATHS = [
    "data/raw",
    "results/logs",
    "results/analysis",
]

# Files to include
ARCHIVE_FILES = [
    "requirements.txt",
]

def setup_logger() -> logging.Logger:
    logger = logging.getLogger("archive_reproducibility")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def collect_paths_to_archive(
    base_dir: Path,
    subdirs: List[str],
    files: List[str],
    logger: logging.Logger
) -> List[Path]:
    """
    Validates that requested paths exist and collects them for archiving.
    Skips non-existent paths with a warning rather than failing, 
    but ensures at least the requirements.txt is present if it exists.
    """
    paths_to_archive = []
    missing_paths = []

    # Check directories
    for subdir in subdirs:
        full_path = base_dir / subdir
        if full_path.exists():
            paths_to_archive.append(full_path)
            logger.info(f"Found directory to archive: {subdir}")
        else:
            missing_paths.append(subdir)
            logger.warning(f"Directory not found, skipping: {subdir}")

    # Check files
    for file in files:
        full_path = base_dir / file
        if full_path.exists():
            paths_to_archive.append(full_path)
            logger.info(f"Found file to archive: {file}")
        else:
            missing_paths.append(file)
            logger.warning(f"File not found, skipping: {file}")

    if not paths_to_archive:
        raise FileNotFoundError(
            "No valid paths found to archive. Ensure data/raw, results/logs, "
            "results/analysis, and requirements.txt exist."
        )

    if missing_paths:
        logger.warning(f"Skipped {len(missing_paths)} missing paths: {missing_paths}")

    return paths_to_archive

def create_archive(
    base_dir: Path,
    paths: List[Path],
    output_name: str,
    logger: logging.Logger
) -> Path:
    """
    Creates a gzipped tarball containing the specified paths.
    """
    output_path = base_dir / "results" / "archive" / output_name
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Creating archive: {output_path}")

    with tarfile.open(output_path, "w:gz") as tar:
        for path in paths:
            # Determine the arcname (path inside the tarball)
            # We want to preserve the relative structure from PROJECT_ROOT
            # e.g., data/raw -> data/raw
            if path.is_dir():
                # Add directory recursively
                for root, dirs, files in os.walk(path):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(base_dir)
                        tar.add(file_path, arcname=arcname)
            else:
                # Add file
                arcname = path.relative_to(base_dir)
                tar.add(path, arcname=arcname)

    logger.info(f"Archive created successfully: {output_path}")
    return output_path

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="T049: Generate reproducibility archive of experiment results."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Base directory for the project (default: auto-detect from script location)."
    )
    parser.add_argument(
        "--timestamp-format",
        type=str,
        default="%Y%m%d_%H%M%S",
        help="Timestamp format for archive filename (default: %%Y%%m%%d_%%H%%M%%S)."
    )
    parser.add_argument(
        "--prefix",
        type=str,
        default="spatialclaw_restriction_run",
        help="Prefix for the archive filename."
    )
    return parser.parse_args()

def main() -> int:
    args = parse_args()
    logger = setup_logger()

    # Determine base directory
    base_dir = Path(args.output_dir) if args.output_dir else PROJECT_ROOT
    if not base_dir.exists():
        logger.error(f"Base directory does not exist: {base_dir}")
        return 1

    logger.info(f"Project root detected at: {base_dir}")

    # Collect paths
    try:
        paths_to_archive = collect_paths_to_archive(
            base_dir, ARCHIVE_PATHS, ARCHIVE_FILES, logger
        )
    except FileNotFoundError as e:
        logger.error(str(e))
        return 1

    # Generate filename
    timestamp = datetime.now().strftime(args.timestamp_format)
    archive_name = f"{args.prefix}_{timestamp}.tar.gz"

    # Create archive
    try:
        output_path = create_archive(base_dir, paths_to_archive, archive_name, logger)
        logger.info(f"SUCCESS: Archive saved to {output_path}")
        return 0
    except Exception as e:
        logger.error(f"Failed to create archive: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())