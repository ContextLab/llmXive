"""
Project Structure Setup Script for llmXive
Creates the required directory hierarchy and placeholder files.
"""
import os
from pathlib import Path
import sys

def setup_directories():
    """
    Creates the project structure per implementation plan:
    - src/ (source code)
    - tests/ (test suite)
    - data/ (raw, derived, gold_standard)
    - specs/001-gene-regulation/ (feature specifications)
    - artifacts/ (intermediate outputs)
    - figures/ (plots and visualizations)
    """
    base_dir = Path(".")
    
    # Define the directory structure
    directories = [
        "src",
        "src/lib",
        "src/services",
        "src/analysis",
        "src/models",
        "src/cli",
        "src/scripts",
        "tests",
        "tests/unit",
        "tests/integration",
        "data",
        "data/raw",
        "data/derived",
        "data/gold_standard",
        "specs/001-gene-regulation",
        "specs/001-gene-regulation/contracts",
        "artifacts",
        "figures",
    ]

    created_count = 0
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    # Create placeholder files to ensure the structure is non-empty and git-tracked
    placeholder_files = {
        "src/__init__.py": "# llmXive source package",
        "src/lib/__init__.py": "# lib utilities",
        "src/services/__init__.py": "# service layer",
        "src/analysis/__init__.py": "# analysis module",
        "src/models/__init__.py": "# model loading",
        "src/cli/__init__.py": "# CLI interface",
        "src/scripts/__init__.py": "# data scripts",
        "tests/__init__.py": "# test package",
        "tests/unit/__init__.py": "# unit tests",
        "tests/integration/__init__.py": "# integration tests",
        "data/raw/.gitkeep": "# Raw data storage",
        "data/derived/.gitkeep": "# Derived data storage",
        "data/gold_standard/.gitkeep": "# Gold standard data storage",
        "specs/001-gene-regulation/README.md": "# Gene Regulation Feature Specs",
        "specs/001-gene-regulation/contracts/.gitkeep": "# Contract schemas",
        "artifacts/.gitkeep": "# Experiment artifacts",
        "figures/.gitkeep": "# Generated figures",
    }

    for file_path, content in placeholder_files.items():
        full_path = base_dir / file_path
        if not full_path.exists():
            full_path.write_text(content)
            print(f"Created placeholder file: {full_path}")
        else:
            print(f"File already exists: {full_path}")

    print(f"\nProject structure setup complete. Created {created_count} new directories.")
    return True

if __name__ == "__main__":
    setup_directories()
