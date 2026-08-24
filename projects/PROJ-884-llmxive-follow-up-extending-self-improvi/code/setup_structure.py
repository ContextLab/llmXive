"""
Setup script to create the code directory hierarchy for the llmXive project.
Creates: code/{dataset,symbolic,bes,analysis,utils}
"""
import os
import sys
import argparse
from pathlib import Path
from typing import List

# Define the required directory structure relative to the project root
# The project root is assumed to be the parent of the 'code' directory
CODE_ROOT = Path(__file__).parent.resolve()
PROJECT_ROOT = CODE_ROOT.parent

REQUIRED_DIRS = [
    "dataset",
    "symbolic",
    "bes",
    "analysis",
    "utils"
]

def setup_code_directories() -> List[str]:
    """
    Creates the required code subdirectories and verifies they exist and are writable.
    
    Returns:
        List[str]: List of created directory paths as strings.
        
    Raises:
        RuntimeError: If a directory cannot be created or is not writable.
    """
    created_dirs = []
    
    for dir_name in REQUIRED_DIRS:
        target_path = CODE_ROOT / dir_name
        
        # Check if directory exists
        if not target_path.exists():
            try:
                target_path.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {target_path}")
            except OSError as e:
                raise RuntimeError(f"Failed to create directory {target_path}: {e}")
        
        # Verify directory exists and is writable
        if not target_path.exists():
            raise RuntimeError(f"Directory {target_path} does not exist after creation attempt.")
        
        if not os.access(target_path, os.W_OK):
            raise RuntimeError(f"Directory {target_path} is not writable.")
        
        created_dirs.append(str(target_path))
    
    return created_dirs

def main():
    """Entry point for the setup script."""
    parser = argparse.ArgumentParser(
        description="Setup code directory hierarchy for llmXive project."
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing directories, do not create new ones."
    )
    args = parser.parse_args()
    
    try:
        created = setup_code_directories()
        print(f"\nSuccessfully verified/created {len(created)} directories:")
        for d in created:
            print(f"  - {d}")
        return 0
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
