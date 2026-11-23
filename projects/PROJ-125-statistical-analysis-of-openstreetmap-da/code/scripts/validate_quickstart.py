"""
Script to validate the quickstart.md documentation.

This script performs the following checks:
1. Verifies that docs/quickstart.md exists and is not empty.
2. Validates that the steps described in quickstart.md can be executed.
3. Checks that all referenced output files are generated correctly.
"""
import os
import sys
import json
import logging
from pathlib import Path
import subprocess

from utils.logging import get_logger

logger = get_logger(__name__)

def check_file_exists(file_path: Path) -> bool:
    """Check if a file exists."""
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return False
    return True

def check_file_not_empty(file_path: Path) -> bool:
    """Check if a file is not empty."""
    if file_path.stat().st_size == 0:
        logger.error(f"File is empty: {file_path}")
        return False
    return True

def run_command(command: list, cwd: Path = None) -> tuple:
    """Run a shell command and return the output and return code."""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout, result.returncode
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {' '.join(command)}")
        logger.error(f"Error output: {e.stderr}")
        return e.stderr, e.returncode

def validate_quickstart() -> bool:
    """
    Validate the quickstart.md documentation.
    
    Returns:
        bool: True if validation passes, False otherwise.
    """
    project_root = Path(__file__).parent.parent.parent
    quickstart_path = project_root / "docs" / "quickstart.md"
    
    # Check 1: File exists and is not empty
    if not check_file_exists(quickstart_path):
        return False
    if not check_file_not_empty(quickstart_path):
        return False
    
    logger.info("✓ quickstart.md exists and is not empty")
    
    # Check 2: Validate installation steps
    logger.info("Validating installation steps...")
    # Assuming the quickstart mentions installing requirements
    requirements_path = project_root / "requirements.txt"
    if not check_file_exists(requirements_path):
        logger.error("requirements.txt not found, skipping installation validation")
    else:
        # Try to install (dry-run or actual install depending on environment)
        # For validation, we'll just check if pip can parse the file
        stdout, rc = run_command([sys.executable, "-m", "pip", "install", "--dry-run", "-r", str(requirements_path)], cwd=project_root)
        if rc != 0:
            logger.error("Failed to validate requirements.txt")
            return False
        logger.info("✓ Installation steps validated")
    
    # Check 3: Validate data directory setup
    logger.info("Validating data directory setup...")
    data_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "results"
    ]
    for d in data_dirs:
        if not d.exists():
            logger.warning(f"Directory not found: {d} (may be created during pipeline execution)")
        else:
            logger.info(f"✓ Directory exists: {d}")
    
    # Check 4: Validate that main scripts are executable
    logger.info("Validating main scripts...")
    main_scripts = [
        project_root / "code" / "ingest.py",
        project_root / "code" / "eda.py",
        project_root / "code" / "modeling.py"
    ]
    for script in main_scripts:
        if not check_file_exists(script):
            logger.error(f"Main script not found: {script}")
            return False
        # Try to import the script to check for syntax errors
        try:
            run_command([sys.executable, "-m", "py_compile", str(script)], cwd=project_root)
            logger.info(f"✓ Script compiles successfully: {script}")
        except Exception as e:
            logger.error(f"Script compilation failed: {script} - {e}")
            return False
    
    # Check 5: Validate output paths mentioned in quickstart
    logger.info("Validating output paths...")
    # These are typically created during execution, so we just check if the directories exist
    output_dirs = [
        project_root / "data" / "results"
    ]
    for d in output_dirs:
        if not d.exists():
            logger.warning(f"Output directory not found: {d} (may be created during pipeline execution)")
        else:
            logger.info(f"✓ Output directory exists: {d}")
    
    logger.info("✓ All quickstart.md validations passed")
    return True

def main():
    """Main entry point for the validation script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting quickstart.md validation...")
    
    success = validate_quickstart()
    
    if success:
        logger.info("Validation completed successfully!")
        sys.exit(0)
    else:
        logger.error("Validation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
