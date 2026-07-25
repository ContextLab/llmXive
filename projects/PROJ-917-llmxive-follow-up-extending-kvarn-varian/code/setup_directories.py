"""
Setup script to create the `code/` root directory and verify its existence.
This task (T001a) ensures the project's code root is initialized.
"""
import os
from pathlib import Path
import sys

# Define the project root relative to this script's location
# Assuming this script is at code/setup_directories.py
# We want to create the parent directory of this script if it doesn't exist,
# but the task specifically asks to create the `code/` root directory.
# Since this script IS inside code/, we assume the project root is the parent.

def create_directories():
    """
    Creates the `code/` directory if it does not exist.
    Since this file is inside `code/`, we ensure the directory exists.
    """
    # Get the directory where this script resides (code/)
    current_file_path = Path(__file__).resolve()
    code_dir = current_file_path.parent
    
    # Ensure the code directory exists
    if not code_dir.exists():
        code_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {code_dir}")
    else:
        print(f"Directory already exists: {code_dir}")
    
    # Verify the directory exists
    if code_dir.is_dir():
        print(f"Verification: {code_dir} exists.")
        return True
    else:
        print(f"Error: {code_dir} was not created successfully.")
        return False

def verify_structure():
    """
    Verifies the structure of the code/ directory.
    For T001a, we just need to ensure the directory exists.
    """
    current_file_path = Path(__file__).resolve()
    code_dir = current_file_path.parent
    return code_dir.is_dir()

def main():
    """
    Main entry point for the setup script.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    
    logger.info("Starting directory setup (T001a)...")
    
    success = create_directories()
    
    if success:
        logger.info("Directory setup completed successfully.")
        # Verify
        if verify_structure():
            logger.info("Verification passed: code/ directory exists.")
            sys.exit(0)
        else:
            logger.error("Verification failed: code/ directory missing.")
            sys.exit(1)
    else:
        logger.error("Directory setup failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()