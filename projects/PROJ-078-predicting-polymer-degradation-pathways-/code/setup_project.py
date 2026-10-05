import os
import sys
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from utils import get_logger, ensure_directory, get_timestamp

def create_directories(base_path: Path, subdirs: List[str]) -> None:
    """Create directory structure."""
    for subdir in subdirs:
        ensure_directory(base_path / subdir)

def verify_directories(base_path: Path, subdirs: List[str]) -> bool:
    """Verify that all required directories exist."""
    logger = get_logger()
    missing = []
    for subdir in subdirs:
        full_path = base_path / subdir
        if not full_path.exists() or not full_path.is_dir():
            missing.append(subdir)
        else:
            logger.info(f"Verified directory: {full_path}")

    if missing:
        logger.error(f"Missing directories: {missing}")
        return False
    return True

def generate_setup_log(base_path: Path, output_path: Path) -> None:
    """Generate the setup log file with directory listing and timestamp."""
    logger = get_logger()
    timestamp = get_timestamp()
    
    # Ensure output directory exists
    ensure_directory(output_path.parent)

    # Generate directory listing
    # We use os.walk to simulate 'ls -R' behavior recursively
    lines = [f"Setup Log - {timestamp}", "=" * 40, ""]
    
    # Walk the base path to simulate recursive listing
    for root, dirs, files in os.walk(base_path):
        # Calculate relative path from base
        rel_root = os.path.relpath(root, base_path)
        if rel_root == '.':
            lines.append(f".")
        else:
            lines.append(f"./{rel_root}/")
        
        # Sort for consistency
        dirs.sort()
        files.sort()
        
        # List directories
        for d in dirs:
            lines.append(f"    {d}/")
        
        # List files
        for f in files:
            lines.append(f"    {f}")
        
        lines.append("")

    content = "\n".join(lines)
    
    with open(output_path, 'w') as f:
        f.write(content)
    
    logger.info(f"Setup log written to {output_path}")

def main():
    """Main entry point for project setup."""
    logger = setup_logging()
    logger.info("Starting project setup verification...")

    # Define base path (project root)
    base_path = Path(__file__).resolve().parent.parent
    
    # Define required directories relative to project root
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/reports",
        "tests",
        "state",
        "state/projects"
    ]

    # Create directories
    create_directories(base_path, required_dirs)

    # Verify directories
    if not verify_directories(base_path, required_dirs):
        logger.error("Directory verification failed.")
        sys.exit(1)

    # Generate setup log
    log_path = base_path / "state" / "setup_log.txt"
    generate_setup_log(base_path, log_path)

    logger.info("Setup complete.")

if __name__ == "__main__":
    main()
