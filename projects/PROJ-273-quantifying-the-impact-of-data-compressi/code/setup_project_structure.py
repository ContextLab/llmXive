"""
Project structure setup script for llmXive research-implementer agent.
Creates the required directory tree as specified in task T001.
"""
import os
from pathlib import Path

def create_directory_structure(root_dir: str = ".") -> None:
    """
    Creates the full project directory structure per the implementation plan.
    
    Directories created:
    - src/data, src/compression, src/pe, src/utils
    - tests/unit, tests/integration, tests/contract
    - data/raw, data/interim, data/processed, data/external
    - reports
    - code/provenance
    """
    base_path = Path(root_dir)
    
    # Define all required directories
    directories = [
        # Source code structure
        "src/data",
        "src/compression",
        "src/pe",
        "src/utils",
        
        # Test structure
        "tests/unit",
        "tests/integration",
        "tests/contract",
        
        # Data structure
        "data/raw",
        "data/interim",
        "data/processed",
        "data/external",
        
        # Reports and provenance
        "reports",
        "code/provenance",
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
        else:
            # Ensure it's actually a directory
            if not full_path.is_dir():
                raise FileExistsError(f"Path exists but is not a directory: {full_path}")
    
    print(f"Project structure created successfully. {created_count} new directories added.")
    print(f"Base path: {base_path.resolve()}")
    
    # Verify structure
    missing = []
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            missing.append(dir_path)
    
    if missing:
        raise RuntimeError(f"Failed to create directories: {missing}")
    
    # List created structure for verification
    print("\nCreated directory structure:")
    for dir_path in sorted(directories):
        full_path = base_path / dir_path
        if full_path.exists():
            print(f"  ✓ {dir_path}")

if __name__ == "__main__":
    create_directory_structure()