"""
Helper module to create tests directory.
"""
import os
import sys
from pathlib import Path

def create_tests_directory():
    """
    Create tests directory and __init__.py.
    """
    project_root = Path.cwd()
    tests_dir = project_root / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    
    init_file = tests_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text("# Tests package\n")
    
    print(f"Created tests directory: {tests_dir}")

def main():
    create_tests_directory()

if __name__ == "__main__":
    main()