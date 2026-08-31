import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

def create_structure(root: Optional[Path] = None) -> List[str]:
    """
    Creates the required project directory structure for llmXive research pipeline.
    
    Args:
        root: Base directory for the project. Defaults to current working directory.
    
    Returns:
        List of created directory paths as strings.
    """
    if root is None:
        root = Path.cwd()
    
    # Define the required directory structure relative to root
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "code/utils",
        "tests",
        "tests/contract",
        "tests/unit",
        "tests/integration",
        "docs",
        "state"
    ]
    
    created_dirs = []
    
    for dir_path in directories:
        full_path = root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(full_path))
        print(f"Created directory: {full_path}")
    
    return created_dirs

def main() -> int:
    """
    Main entry point for the script.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        root = Path.cwd()
        print(f"Creating project structure in: {root}")
        created = create_structure(root)
        print(f"\nSuccessfully created {len(created)} directories.")
        return 0
    except Exception as e:
        print(f"Error creating project structure: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
