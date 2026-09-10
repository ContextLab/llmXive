"""
Setup script to create the code directory hierarchy for the llmXive project.
Creates: code/{dataset,symbolic,bes,analysis,utils}
Verifies existence and writability.
"""
import os
import sys
import argparse
from pathlib import Path
from typing import List

# Define the required subdirectories relative to the project root
REQUIRED_SUBDIRS = [
    "dataset",
    "symbolic",
    "bes",
    "analysis",
    "utils"
]

def setup_code_directories(base_path: Path) -> List[Path]:
    """
    Create the code directory hierarchy and verify writability.

    Args:
        base_path: The project root path.

    Returns:
        List of created directory paths.

    Raises:
        RuntimeError: If a directory cannot be created or is not writable.
    """
    code_root = base_path / "code"
    created_dirs = []

    # Ensure the root code directory exists
    if not code_root.exists():
        code_root.mkdir(parents=True, exist_ok=True)
        if not os.access(code_root, os.W_OK):
            raise RuntimeError(f"Code root directory {code_root} exists but is not writable.")
    else:
        if not os.access(code_root, os.W_OK):
            raise RuntimeError(f"Code root directory {code_root} exists but is not writable.")

    # Create and verify subdirectories
    for subdir_name in REQUIRED_SUBDIRS:
        subdir_path = code_root / subdir_name
        
        if not subdir_path.exists():
            subdir_path.mkdir(parents=True, exist_ok=True)
            if not subdir_path.exists():
                raise RuntimeError(f"Failed to create directory: {subdir_path}")
        
        # Verify writability
        if not os.access(subdir_path, os.W_OK):
            raise RuntimeError(f"Directory {subdir_path} exists but is not writable.")
        
        created_dirs.append(subdir_path)
        print(f"Verified: {subdir_path} (writable)")

    return created_dirs

def main():
    parser = argparse.ArgumentParser(
        description="Setup the code directory hierarchy for the llmXive project."
    )
    parser.add_argument(
        "--base-path",
        type=Path,
        default=Path.cwd(),
        help="The project root path (default: current working directory)."
    )
    
    args = parser.parse_args()
    
    print(f"Setting up code directories in: {args.base_path}")
    
    try:
        created = setup_code_directories(args.base_path)
        print(f"\nSuccessfully created/verified {len(created)} directories:")
        for d in created:
            print(f"  - {d}")
        return 0
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
