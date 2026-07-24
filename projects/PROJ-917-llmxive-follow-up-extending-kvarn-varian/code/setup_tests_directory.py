"""
Script to create the tests directory structure as required by task T002.
Creates:
  - code/tests/
  - code/tests/test_data_generation/
  - code/tests/test_model_training/
  - code/tests/test_simulation/
"""
import os
from pathlib import Path

def create_directories():
    """Create the required test directory structure."""
    base_dir = Path(__file__).parent.parent
    tests_root = base_dir / "tests"
    
    subdirs = [
        "test_data_generation",
        "test_model_training",
        "test_simulation"
    ]
    
    created = []
    for subdir in subdirs:
        path = tests_root / subdir
        path.mkdir(parents=True, exist_ok=True)
        created.append(str(path))
        # Create __init__.py to make them packages
        init_file = path / "__init__.py"
        if not init_file.exists():
            init_file.write_text('"""Tests for {name}."""\n'.format(name=subdir))
    
    # Ensure root tests __init__.py exists
    root_init = tests_root / "__init__.py"
    if not root_init.exists():
        root_init.write_text('"""Test suite."""\n')
        created.append(str(root_init))
        
    return created

def main():
    """Entry point for the script."""
    print("Creating tests directory structure...")
    created = create_directories()
    for path in created:
        print(f"Created: {path}")
    print("Done.")

if __name__ == "__main__":
    main()