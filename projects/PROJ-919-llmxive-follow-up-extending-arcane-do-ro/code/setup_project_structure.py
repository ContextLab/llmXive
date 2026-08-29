"""
Setup script to initialize the llmXive project directory structure.
Creates required directories for source code, tests, data, and specifications.
"""
import os
from pathlib import Path
import sys

# Define the project root relative to this script's location
# The script is located at code/setup_project_structure.py
# We want to create structure relative to the 'code' directory root
PROJECT_ROOT = Path(__file__).parent.resolve()

# Directories to create as per task T001
DIRECTORIES = [
    "src",
    "src/lib",
    "src/services",
    "src/cli",
    "src/models",
    "src/analysis",
    "tests",
    "tests/unit",
    "tests/integration",
    "data",
    "data/raw",
    "data/derived",
    "data/gold_standard",
    "artifacts",
    "specs",
    "specs/001-gene-regulation",
    "specs/001-gene-regulation/contracts",
]

def setup_directories():
    """Create the project directory structure."""
    created_count = 0
    for dir_name in DIRECTORIES:
        dir_path = PROJECT_ROOT / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    # Create placeholder files to ensure directories are not empty and structure is visible
    placeholder_files = [
        ("src/__init__.py", "# llmXive source package"),
        ("src/lib/__init__.py", "# Library utilities"),
        ("src/services/__init__.py", "# Service layer"),
        ("src/cli/__init__.py", "# CLI interface"),
        ("src/models/__init__.py", "# Model definitions"),
        ("src/analysis/__init__.py", "# Analysis tools"),
        ("tests/__init__.py", "# Test package"),
        ("tests/unit/__init__.py", "# Unit tests"),
        ("tests/integration/__init__.py", "# Integration tests"),
        ("data/raw/.gitkeep", "# Raw data storage"),
        ("data/derived/.gitkeep", "# Derived data storage"),
        ("data/gold_standard/.gitkeep", "# Gold standard data storage"),
        ("artifacts/.gitkeep", "# Artifacts storage"),
        ("specs/001-gene-regulation/.gitkeep", "# Feature specs"),
        ("specs/001-gene-regulation/contracts/.gitkeep", "# Contract schemas"),
    ]

    for file_path, content in placeholder_files:
        full_path = PROJECT_ROOT / file_path
        if not full_path.exists():
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content + "\n")
            print(f"Created placeholder file: {full_path}")
            created_count += 1

    print(f"\nProject structure setup complete. Created {created_count} new items.")
    return created_count

if __name__ == "__main__":
    setup_directories()
