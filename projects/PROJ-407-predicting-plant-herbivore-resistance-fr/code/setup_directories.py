import os
from pathlib import Path
import sys

def ensure_directories():
    """
    Create the required directory structure for the project.
    This satisfies T006: Setup directory structure.
    
    Creates:
    - code/
    - data/raw/
    - data/interim/
    - data/processed/
    - data/results/
    - tests/unit/
    - tests/integration/
    - tests/contract/
    
    Returns:
        bool: True if all directories were created successfully.
    """
    # Define the base project root relative to where this script is run.
    # Assuming the script is run from the project root or the project root is the CWD.
    # If running as a module, we might need to adjust, but for T006 we assume CWD is project root.
    base_path = Path(".")
    
    directories = [
        "code",
        "data/raw",
        "data/interim",
        "data/processed",
        "data/results",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]
    
    created_count = 0
    for dir_name in directories:
        target_path = base_path / dir_name
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
        # Note: We do not raise an error if it exists, as per idempotent design.
        
    print(f"Directory structure setup complete. Created {created_count} new directories.")
    return True

def main():
    """Entry point for the directory setup script."""
    try:
        ensure_directories()
        print("T006: Directory structure verified and created.")
        return 0
    except Exception as e:
        print(f"Error during directory setup: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())