"""
Project Structure Setup Script for llmXive.

Creates the required directory hierarchy for the ArcANE gene regulation project.
Ensures all top-level and nested directories exist before data processing begins.
"""
import os
import sys
from pathlib import Path
import logging

# Configure logging for the setup script
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the project root relative to this script's location or current working directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent if '__file__' in globals() else Path.cwd()

# Define the required directory structure relative to the project root
# This matches the specification: src/, tests/, data/, specs/001-gene-regulation/
DIRECTORIES = [
    "src",
    "src/lib",
    "src/services",
    "src/analysis",
    "src/models",
    "src/cli",
    "src/scripts",
    "tests",
    "tests/unit",
    "tests/integration",
    "data",
    "data/raw",
    "data/derived",
    "data/gold_standard",
    "artifacts",
    "specs",
    "specs/001-gene-regulation",
    "specs/001-gene-regulation/contracts",
    "code", 
    "scripts"
]

def setup_directories(root_path: Path = None) -> dict:
    """
    Creates all required directories for the project structure.
    
    Args:
        root_path: The base path for the project. Defaults to current working directory.
        
    Returns:
        dict: A summary of created directories and any errors encountered.
    """
    if root_path is None:
        root_path = PROJECT_ROOT
    
    created_dirs = []
    errors = []
    
    logger.info(f"Setting up project structure at: {root_path}")
    
    for dir_path in DIRECTORIES:
        full_path = root_path / dir_path
        try:
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                created_dirs.append(str(full_path))
                logger.debug(f"Created directory: {full_path}")
            else:
                logger.debug(f"Directory already exists: {full_path}")
        except OSError as e:
            error_msg = f"Failed to create {full_path}: {e}"
            errors.append(error_msg)
            logger.error(error_msg)
    
    summary = {
        "root": str(root_path),
        "directories_created": created_dirs,
        "directories_skipped": len(DIRECTORIES) - len(created_dirs),
        "errors": errors,
        "total_directories": len(DIRECTORIES)
    }
    
    return summary

def main():
    """
    Main entry point for the setup script.
    """
    summary = setup_directories()
    
    if summary["errors"]:
        logger.error(f"Setup completed with {len(summary['errors'])} errors.")
        for err in summary["errors"]:
            print(f"ERROR: {err}", file=sys.stderr)
        sys.exit(1)
    else:
        logger.info(f"Successfully created {len(summary['directories_created'])} directories.")
        logger.info("Project structure is ready.")
        print(f"Project structure created at: {summary['root']}")
        print(f"Directories created: {len(summary['directories_created'])}")
        return 0

if __name__ == "__main__":
    sys.exit(main() or 0)
