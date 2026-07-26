"""
Project setup utilities for llmXive research-implementer.
Creates the required directory structure for the polymer degradation project.
"""
import os
import sys
from pathlib import Path
from typing import List, Optional

def create_directories(root_dir: Optional[Path] = None) -> List[str]:
    """
    Create the standard project directory structure.
    
    Args:
        root_dir: Base directory for the project. Defaults to current working directory.
        
    Returns:
        List of created directory paths.
    """
    if root_dir is None:
        root_dir = Path.cwd()
    
    # Define required directories relative to root
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/reports",
        "tests",
        "state"
    ]
    
    created_paths = []
    
    for dir_path in required_dirs:
        full_path = root_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(str(full_path))
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
            created_paths.append(str(full_path))
    
    return created_paths

def verify_directories(root_dir: Optional[Path] = None) -> bool:
    """
    Verify that all required directories exist.
    
    Args:
        root_dir: Base directory for the project. Defaults to current working directory.
        
    Returns:
        True if all directories exist, False otherwise.
    """
    if root_dir is None:
        root_dir = Path.cwd()
    
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/reports",
        "tests",
        "state"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        full_path = root_dir / dir_path
        if not full_path.exists() or not full_path.is_dir():
            print(f"Missing or invalid directory: {full_path}")
            all_exist = False
        else:
            print(f"Verified: {full_path}")
    
    return all_exist

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup project directory structure")
    parser.add_argument("--root", type=str, default=None, help="Root directory for project")
    parser.add_argument("--verify", action="store_true", help="Only verify directories exist")
    
    args = parser.parse_args()
    
    root_path = Path(args.root) if args.root else None
    
    if args.verify:
        success = verify_directories(root_path)
        sys.exit(0 if success else 1)
    else:
        created = create_directories(root_path)
        print(f"\nSetup complete. Created {len(created)} directories.")
        sys.exit(0)
