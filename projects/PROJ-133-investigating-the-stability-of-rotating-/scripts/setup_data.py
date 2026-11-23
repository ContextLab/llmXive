#!/usr/bin/env python3
"""
Standalone script to set up the data directory structure.

This script is the primary entry point for users to initialize the
project's data directory structure as required by T004.

Usage:
    python scripts/setup_data.py
"""
import os
import sys
from pathlib import Path

def main():
    """Main entry point for the script."""
    # Ensure we are running from the project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print(f"Running from project root: {project_root}")
    
    # Import and run the setup function
    sys.path.insert(0, str(project_root / "code"))
    from utils.setup_data_dirs import create_project_structure
    
    print("Setting up data directory structure...")
    create_project_structure()
    print("Data directory structure setup complete.")
    
    # Verify the structure
    data_dir = Path("data")
    if data_dir.exists():
        print("\nVerified directory structure:")
        for root, dirs, files in os.walk(data_dir):
            level = root.replace(str(data_dir), '').count(os.sep)
            indent = ' ' * 2 * level
            print(f'{indent}{os.path.basename(root)}/')
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f'{subindent}{file}')
    else:
        print("ERROR: data directory was not created!")
        sys.exit(1)

if __name__ == "__main__":
    main()