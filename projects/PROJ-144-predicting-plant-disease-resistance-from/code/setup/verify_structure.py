import os
import sys
import subprocess
import logging
from pathlib import Path

# Import the ensure_dirs function from constants to verify the expected structure
from utils.constants import ensure_dirs, PROJECT_ROOT

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "data/intermediate",
    "tests",
    "state",
    "results",
    "results/plots",
    "contracts",
    "specs"
]

def check_directory_writable(dir_path: Path) -> bool:
    """
    Check if a directory exists and is writable by attempting to create a temporary file.
    """
    if not dir_path.exists():
        logger.error(f"Directory does not exist: {dir_path}")
        return False
    
    if not dir_path.is_dir():
        logger.error(f"Path is not a directory: {dir_path}")
        return False

    test_file = dir_path / ".write_test"
    try:
        test_file.touch(exist_ok=True)
        test_file.unlink()
        logger.info(f"Directory is writable: {dir_path}")
        return True
    except (OSError, PermissionError) as e:
        logger.error(f"Directory is not writable: {dir_path} - Error: {e}")
        return False

def run_ls_recursive(root_path: Path) -> str:
    """
    Run 'ls -R' equivalent on the root path and capture the output.
    Returns the output string.
    """
    try:
        # Use os.walk to simulate ls -R output format manually or call system ls if available
        # Since we need to be cross-platform safe, we'll construct the output
        output_lines = []
        for root, dirs, files in os.walk(root_path):
            # Filter out hidden files/dirs for cleaner output if desired, 
            # but standard ls -R includes them. We'll include everything.
            level = root.replace(str(root_path), '').count(os.sep)
            indent = ' ' * 2 * level
            output_lines.append(f"{indent}{os.path.basename(root)}/")
            sub_indent = ' ' * 2 * (level + 1)
            for f in sorted(files):
                output_lines.append(f"{sub_indent}{f}")
            for d in sorted(dirs):
                output_lines.append(f"{sub_indent}{d}/")
        return '\n'.join(output_lines)
    except Exception as e:
        logger.error(f"Error walking directory: {e}")
        return f"Error walking directory: {e}"

def main():
    logger.info("Starting directory structure verification...")
    
    # Ensure the expected directories exist first (idempotent)
    ensure_dirs()
    
    all_writable = True
    missing_dirs = []

    for dir_name in REQUIRED_DIRS:
        dir_path = PROJECT_ROOT / dir_name
        if not dir_path.exists():
            missing_dirs.append(dir_name)
            all_writable = False
        elif not check_directory_writable(dir_path):
            all_writable = False

    if missing_dirs:
        logger.error(f"Missing directories: {missing_dirs}")
        # Attempt to create them if missing, as T001a might have failed partially
        for d in missing_dirs:
            p = PROJECT_ROOT / d
            p.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created missing directory: {p}")
            if not check_directory_writable(p):
                all_writable = False

    if not all_writable:
        logger.error("Verification FAILED: Some directories are missing or not writable.")
        sys.exit(1)

    logger.info("All required directories exist and are writable.")
    
    # Capture and log the directory tree
    tree_output = run_ls_recursive(PROJECT_ROOT)
    logger.info("Directory Structure (ls -R equivalent):")
    logger.info("-" * 40)
    logger.info(tree_output)
    logger.info("-" * 40)

    # Write the verification report to a file in the state directory
    report_path = PROJECT_ROOT / "state" / "structure_verification.log"
    try:
        with open(report_path, 'w') as f:
            f.write("Directory Structure Verification Report\n")
            f.write("=" * 50 + "\n")
            f.write(f"Timestamp: {subprocess.check_output(['date']).decode().strip() if sys.platform != 'win32' else 'N/A'}\n")
            f.write("\nDirectory Listing:\n")
            f.write(tree_output)
            f.write("\n\nStatus: SUCCESS\n")
        logger.info(f"Verification report saved to: {report_path}")
    except Exception as e:
        logger.error(f"Failed to save verification report: {e}")
        sys.exit(1)

    logger.info("Task T001b completed successfully.")

if __name__ == "__main__":
    main()
