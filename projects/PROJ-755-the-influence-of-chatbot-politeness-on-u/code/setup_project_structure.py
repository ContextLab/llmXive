import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

def create_structure(base_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Creates the project directory structure for the llmXive pipeline.
    
    Args:
        base_path: Optional base path. Defaults to current working directory.
        
    Returns:
        Dictionary mapping directory names to their absolute paths.
    """
    if base_path is None:
        base_path = Path.cwd()
    
    required_dirs = [
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
    
    created_paths = {}
    
    for dir_name in required_dirs:
        full_path = base_path / dir_name
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_paths[dir_name] = str(full_path.resolve())
            print(f"Created directory: {full_path}")
        except OSError as e:
            print(f"Error creating directory {full_path}: {e}", file=sys.stderr)
            raise
    
    return created_paths

def main() -> int:
    """
    Main entry point for the setup script.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        print("Initializing project directory structure...")
        created = create_structure()
        print("\nDirectory structure created successfully:")
        for name, path in created.items():
            print(f"  {name}: {path}")
        return 0
    except Exception as e:
        print(f"Failed to create directory structure: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
