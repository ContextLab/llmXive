"""
Helper module to create state directory.
"""
import os
import sys
from pathlib import Path

def create_state_directory():
    """
    Create state directory and __init__.py.
    """
    project_root = Path.cwd()
    state_dir = project_root / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    
    init_file = state_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text("# State package\n")
    
    print(f"Created state directory: {state_dir}")

def main():
    create_state_directory()

if __name__ == "__main__":
    main()