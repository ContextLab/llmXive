"""
Helper module to create artifacts directory.
"""
import os
import sys
from pathlib import Path

def create_artifacts_directory():
    """
    Create artifacts directory and __init__.py.
    """
    project_root = Path.cwd()
    artifacts_dir = project_root / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    init_file = artifacts_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text("# Artifacts package\n")
    
    print(f"Created artifacts directory: {artifacts_dir}")

def main():
    create_artifacts_directory()

if __name__ == "__main__":
    main()