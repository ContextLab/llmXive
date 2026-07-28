"""
Script to initialize the llmXive project directory structure.
Creates all required directories for src, tests, data, and specs as per the implementation plan.
"""
import os
from pathlib import Path

def setup_directories():
    """
    Creates the full project directory structure required for llmXive.
    Includes src, tests, data (with subdirs), and specs.
    """
    root = Path(".")
    
    # Define all required directories
    directories = [
        # Source code
        "code/src",
        "code/src/lib",
        "code/src/services",
        "code/src/cli",
        "code/src/models",
        "code/src/analysis",
        
        # Tests
        "code/tests",
        "code/tests/unit",
        "code/tests/integration",
        
        # Data directories (Phase 2 prerequisites)
        "code/data/raw",
        "code/data/derived",
        "code/data/gold_standard",
        "code/artifacts",
        
        # Specifications
        "code/specs/001-gene-regulation",
        "code/specs/001-gene-regulation/contracts",
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory exists: {full_path}")
    
    # Create placeholder __init__.py files to make them Python packages
    init_files = [
        "code/src/__init__.py",
        "code/src/lib/__init__.py",
        "code/src/services/__init__.py",
        "code/src/cli/__init__.py",
        "code/src/models/__init__.py",
        "code/src/analysis/__init__.py",
        "code/tests/__init__.py",
        "code/tests/unit/__init__.py",
        "code/tests/integration/__init__.py",
    ]
    
    for init_file in init_files:
        full_path = root / init_file
        if not full_path.exists():
            full_path.touch()
            print(f"Created package init: {full_path}")
    
    print(f"\nSetup complete. Created {created_count} new directories.")
    return True

if __name__ == "__main__":
    setup_directories()