#!/usr/bin/env python3
"""
Script to set up data directory structure and .gitkeep files.
This script ensures all required data subdirectories exist with .gitkeep files
for proper git tracking.
"""
import os
import sys

# Add code directory to path
code_dir = os.path.join(os.path.dirname(__file__), '..', 'code')
sys.path.insert(0, code_dir)

from setup_data_dirs import main

if __name__ == "__main__":
    print("=" * 60)
    print("Setting up llmXive data directory structure")
    print("=" * 60)
    main()
    print("=" * 60)
    print("Data directory setup completed successfully!")
    print("=" * 60)