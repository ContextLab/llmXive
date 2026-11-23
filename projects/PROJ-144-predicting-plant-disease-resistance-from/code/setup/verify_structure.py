"""
Verify that all project directories created in T001a/T001b exist and are writable.
Generates state/directory_structure.txt with the recursive directory listing.
"""
import os
import sys
import subprocess
import logging
from pathlib import Path
from utils.constants import ensure_dirs, PROJECT_ROOT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('state/verify_structure.log')
    ]
)
logger = logging.getLogger(__name__)

def check_directory_writable(dir_path: Path) -> bool:
    """
    Check if a directory exists and is writable by attempting to create a temporary file.
    
    Args:
        dir_path: Path to the directory to check
        
    Returns:
        True if directory exists and is writable, False otherwise
    """
    if not dir_path.exists():
        logger.error(f"Directory does not exist: {dir_path}")
        return False
    
    if not dir_path.is_dir():
        logger.error(f"Path exists but is not a directory: {dir_path}")
        return False
    
    test_file = dir_path / ".write_test"
    try:
        test_file.touch()
        test_file.unlink()
        logger.info(f"Directory writable: {dir_path}")
        return True
    except (OSError, PermissionError) as e:
        logger.error(f"Directory not writable: {dir_path} - {str(e)}")
        return False

def run_ls_recursive(output_path: Path) -> bool:
    """
    Run 'find . -type d | sort' and write output to the specified file.
    
    Args:
        output_path: Path where the directory structure should be written
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Run find command to get all directories
        result = subprocess.run(
            ["find", ".", "-type", "d", "|", "sort"],
            shell=True,
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        
        if result.returncode != 0:
            logger.error(f"find command failed: {result.stderr}")
            return False
        
        # Write output to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result.stdout)
        
        logger.info(f"Directory structure written to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error running ls recursive: {str(e)}")
        return False

def main():
    """
    Main function to verify directory structure and generate listing.
    """
    logger.info("Starting directory structure verification...")
    
    # Expected directories from T001a and T001b
    expected_dirs = [
        "code", "data", "tests", "state", "results", "contracts",
        "data/raw", "data/processed", "data/intermediate", "results/plots"
    ]
    
    all_writable = True
    for dir_name in expected_dirs:
        dir_path = PROJECT_ROOT / dir_name
        if not check_directory_writable(dir_path):
            all_writable = False
    
    if not all_writable:
        logger.error("Some directories are missing or not writable. Aborting.")
        sys.exit(1)
    
    # Generate directory structure file
    output_path = PROJECT_ROOT / "state" / "directory_structure.txt"
    if not run_ls_recursive(output_path):
        logger.error("Failed to generate directory structure file.")
        sys.exit(1)
    
    # Verify output file is non-empty
    if not output_path.exists() or output_path.stat().st_size == 0:
        logger.error("Directory structure file is empty or missing.")
        sys.exit(1)
    
    # Verify expected directories are in the output
    with open(output_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    missing_dirs = []
    for dir_name in expected_dirs:
        if dir_name not in content:
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        logger.error(f"Expected directories missing from output: {missing_dirs}")
        sys.exit(1)
    
    logger.info("Directory structure verification completed successfully.")
    logger.info(f"Output written to: {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
