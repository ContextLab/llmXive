#!/usr/bin/env python3
"""
Project Setup Script for PROJ-267

Creates the initial directory structure for the Atmospheric River Gravity
Correlation research project. This script must be run from the repository
root to properly establish the project tree under projects/.

Usage:
    python projects/PROJ-267-exploring-the-relationship-between-atmos/code/setup_project.py

This script implements T001-T005 by creating the required directory structure.
"""

import os
import sys
from pathlib import Path

# Project root relative to where this script is run
PROJECT_ROOT = Path(__file__).parent.parent

# Directory structure to create (relative to PROJECT_ROOT)
DIRECTORIES = [
    "code",
    "data/raw",
    "data/processed",
    "tests",
    "docs",
    "contracts",
    "state",
    "specs/001-atmospheric-river-gravity",
]

def create_directories():
    """Create all required directories for the project."""
    created = []
    for dir_path in DIRECTORIES:
        full_path = PROJECT_ROOT / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        created.append(full_path)
        print(f"✓ Created: {full_path}")
    return created

def main():
    """Main entry point for project initialization."""
    print("=" * 60)
    print("PROJ-267: Atmospheric River Gravity Correlation")
    print("Project Setup Script")
    print("=" * 60)
    print(f"\nProject root: {PROJECT_ROOT.resolve()}")
    print("\nCreating directory structure...")
    print("-" * 60)

    try:
        created = create_directories()
        print("-" * 60)
        print(f"\n✓ Successfully created {len(created)} directories")
        print("\nNext steps:")
        print("  1. Run T006: Initialize requirements.txt with dependencies")
        print("  2. Run T007: Configure linting (flake8, pyproject.toml)")
        print("  3. Run T008: Create citation verification script")
        print("  4. Run T009: Create quickstart.md documentation")
        print("\nFor more information, see quickstart.md after creation.")
        return 0
    except Exception as e:
        print(f"\n✗ Setup failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
