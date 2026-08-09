import os
import sys
import time
from pathlib import Path
from typing import List

def create_directories(base_path: Path, directories: List[str]) -> List[Path]:
    """
    Create a list of directories relative to the base_path.
    Returns a list of the created Path objects.
    """
    created_paths = []
    for dir_name in directories:
        full_path = base_path / dir_name
        full_path.mkdir(parents=True, exist_ok=True)
        created_paths.append(full_path)
    return created_paths

def verify_directories(paths: List[Path]) -> bool:
    """
    Verify that all provided paths exist and are directories.
    """
    return all(p.exists() and p.is_dir() for p in paths)

def generate_verification_log(paths: List[Path], log_path: Path) -> None:
    """
    Generate a log file containing the list of created paths and their timestamps.
    """
    with open(log_path, 'w') as f:
        f.write("Directory Verification Log\n")
        f.write(f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("-" * 40 + "\n")
        for p in paths:
            f.write(f"Path: {p}\n")
            f.write(f"Exists: {p.exists()}\n")
            f.write(f"Is Directory: {p.is_dir()}\n")
            f.write("-" * 20 + "\n")

def main():
    """
    Main entry point for T001: Initialize Data Directory Structure.
    Creates required directories and generates the verification log.
    """
    project_root = Path(__file__).resolve().parent.parent
    
    # Define required directories
    required_dirs = [
        "data/raw",
        "data/interim",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "reports"
    ]
    
    # Create directories
    created_paths = create_directories(project_root, required_dirs)
    
    # Verify creation
    if not verify_directories(created_paths):
        print("Error: Failed to create one or more required directories.", file=sys.stderr)
        sys.exit(1)
    
    # Generate verification log
    log_path = project_root / "data" / ".verify_structure.log"
    generate_verification_log(created_paths, log_path)
    
    print(f"Successfully created directories and log at: {log_path}")

if __name__ == "__main__":
    main()
