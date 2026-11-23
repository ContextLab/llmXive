"""
Helper module to create results directory.
"""
import os
import sys
from pathlib import Path

def create_results_directory():
    """
    Create results directory and __init__.py.
    """
    project_root = Path.cwd()
    results_dir = project_root / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    init_file = results_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text("# Results package\n")
    
    print(f"Created results directory: {results_dir}")

def main():
    create_results_directory()

if __name__ == "__main__":
    main()