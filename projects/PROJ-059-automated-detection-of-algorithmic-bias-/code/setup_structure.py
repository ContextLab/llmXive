"""
Project Structure Setup Script for PROJ-059
Creates the required directory hierarchy for the automated bias detection pipeline.
"""
import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the project directory structure as defined in T001.
    
    Structure:
    src/bias_pipeline
    src/cli
    data/raw
    data/processed
    data/validation
    tests/unit
    tests/integration
    state
    """
    # Define the base project root (assuming script is in code/)
    # We navigate up one level to the project root
    base_dir = Path(__file__).resolve().parent.parent
    
    # Relative paths to create
    relative_paths = [
        "src/bias_pipeline",
        "src/cli",
        "data/raw",
        "data/processed",
        "data/validation",
        "tests/unit",
        "tests/integration",
        "state"
    ]
    
    created_count = 0
    for rel_path in relative_paths:
        target_path = base_dir / rel_path
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {target_path}")
        else:
            print(f"Directory already exists: {target_path}")
    
    # Create __init__.py files to ensure packages are recognized
    # This is critical for Python imports to work immediately
    init_files = [
        base_dir / "src" / "__init__.py",
        base_dir / "src" / "bias_pipeline" / "__init__.py",
        base_dir / "src" / "cli" / "__init__.py",
        base_dir / "tests" / "__init__.py",
        base_dir / "tests" / "unit" / "__init__.py",
        base_dir / "tests" / "integration" / "__init__.py",
    ]
    
    for init_file in init_files:
        if not init_file.exists():
            init_file.touch()
            print(f"Created init file: {init_file}")
        
    print(f"\nProject structure setup complete. {created_count} new directories created.")
    return True

if __name__ == "__main__":
    create_directories()
