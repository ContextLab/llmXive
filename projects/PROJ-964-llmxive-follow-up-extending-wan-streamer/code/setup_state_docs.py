import os
import sys
from pathlib import Path

def setup_state_docs_directories():
    """
    Creates the 'state/' and 'docs/' directories at the project root.
    These directories are required for Constitution Principle V (state tracking)
    and for storing research documentation.

    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    # Determine project root (assuming script is run from project root or code/ subdirectory)
    # If running from code/, go up one level
    current_dir = Path.cwd()
    if current_dir.name == "code":
        project_root = current_dir.parent
    else:
        project_root = current_dir

    # Define the directories to create
    directories = [
        project_root / "state",
        project_root / "docs"
    ]

    success = True
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            # Verification step: assert existence
            if not directory.is_dir():
                print(f"ERROR: Failed to create or verify directory: {directory}")
                success = False
            else:
                print(f"SUCCESS: Directory created/verified: {directory}")
        except OSError as e:
            print(f"ERROR: Could not create directory {directory}: {e}")
            success = False

    return success

def main():
    """
    Entry point for the script.
    """
    print("Starting setup of 'state/' and 'docs/' directories...")
    success = setup_state_docs_directories()
    
    if success:
        print("All directories created and verified successfully.")
        sys.exit(0)
    else:
        print("Failed to create one or more directories.")
        sys.exit(1)

if __name__ == "__main__":
    main()
