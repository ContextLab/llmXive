import os
import sys
import subprocess
import logging
from pathlib import Path
from utils.constants import ensure_dirs, PROJECT_ROOT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_directory_writable(dir_path: Path) -> bool:
    """
    Check if a directory exists and is writable.
    
    Args:
        dir_path: Path to the directory to check
        
    Returns:
        bool: True if directory exists and is writable, False otherwise
    """
    try:
        # Check if directory exists
        if not dir_path.exists():
            logger.error(f"Directory does not exist: {dir_path}")
            return False
        
        # Check if it's a directory
        if not dir_path.is_dir():
            logger.error(f"Path is not a directory: {dir_path}")
            return False
        
        # Check writability by attempting to create a temporary file
        test_file = dir_path / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
            logger.info(f"Directory is writable: {dir_path}")
            return True
        except (OSError, PermissionError) as e:
            logger.error(f"Directory is not writable: {dir_path} - {e}")
            return False
    except Exception as e:
        logger.error(f"Error checking directory {dir_path}: {e}")
        return False

def run_ls_recursive(base_path: Path, output_file: Path) -> bool:
    """
    Run 'ls -R' recursively on a directory and capture output to a file.
    
    Args:
        base_path: Root directory to start listing from
        output_file: Path to the output file to write the listing
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Running 'ls -R' on {base_path} and writing to {output_file}")
        
        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Run ls -R command
        result = subprocess.run(
            ['ls', '-R', str(base_path)],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Write output to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result.stdout)
        
        logger.info(f"Directory structure successfully written to {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command 'ls -R' failed: {e}")
        logger.error(f"stderr: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Error running ls -R: {e}")
        return False

def main():
    """
    Main function to verify directory structure created in T001a/T001b.
    
    This function:
    1. Ensures all required directories exist (via ensure_dirs from constants)
    2. Checks that each directory is writable
    3. Runs 'ls -R' to capture the directory structure
    4. Writes the output to state/directory_structure.txt
    """
    logger.info("Starting directory structure verification (T001c)")
    
    # Ensure all directories exist
    logger.info("Ensuring directory structure exists...")
    ensure_dirs()
    
    # List of required directories to verify
    required_dirs = [
        PROJECT_ROOT / "code",
        PROJECT_ROOT / "data",
        PROJECT_ROOT / "data" / "raw",
        PROJECT_ROOT / "data" / "processed",
        PROJECT_ROOT / "data" / "intermediate",
        PROJECT_ROOT / "tests",
        PROJECT_ROOT / "state",
        PROJECT_ROOT / "results",
        PROJECT_ROOT / "results" / "plots",
        PROJECT_ROOT / "contracts"
    ]
    
    # Check each directory
    all_writable = True
    for dir_path in required_dirs:
        if not check_directory_writable(dir_path):
            all_writable = False
            logger.error(f"FAILED: Directory check failed for {dir_path}")
        else:
            logger.info(f"PASSED: Directory check passed for {dir_path}")
    
    if not all_writable:
        logger.error("One or more directories are missing or not writable. Aborting.")
        sys.exit(1)
    
    # Run ls -R and capture output
    output_file = PROJECT_ROOT / "state" / "directory_structure.txt"
    if not run_ls_recursive(PROJECT_ROOT, output_file):
        logger.error("Failed to generate directory structure listing.")
        sys.exit(1)
    
    logger.info("Directory structure verification completed successfully.")
    logger.info(f"Output written to: {output_file}")
    print(f"Directory structure verification complete. Output: {output_file}")

if __name__ == "__main__":
    main()