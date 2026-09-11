"""
Project Structure Setup Script for llmXive PROJ-163.

This script creates the required directory structure for the research project:
- code/: Source code modules
- data/raw/: Raw data snapshots from IBM Quantum API
- data/processed/: Processed data (CSVs, metrics)
- tests/: Unit and integration tests
- specs/: Feature specifications and contracts
- docs/: Final reports and documentation
- figures/: Generated plots and visualizations
- state/: Project state tracking (artifacts, hashes)

Usage:
    python code/setup_project.py
"""

import os
from pathlib import Path


def create_project_structure():
    """Create the standard project directory structure."""
    root = Path(__file__).resolve().parent.parent

    # Define required directories
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "tests",
        "specs/001-explore-network-structure-superconducting-qubit-coupling",
        "specs/001-explore-network-structure-superconducting-qubit-coupling/contracts",
        "docs",
        "figures",
        "state/projects"
    ]

    created = []
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path.relative_to(root)))
        else:
            # Ensure it's a directory
            if not full_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")

    # Create .gitkeep files to ensure directories are tracked by git
    keep_files = []
    for dir_path in directories:
        full_path = root / dir_path / ".gitkeep"
        if not full_path.exists():
            full_path.write_text("# Keep this directory in git\n")
            keep_files.append(str(full_path.relative_to(root)))

    return created, keep_files


def main():
    """Entry point for the setup script."""
    print("Initializing project structure for PROJ-163...")
    created, kept = create_project_structure()

    if created:
        print(f"Created directories:")
        for d in created:
            print(f"  - {d}")
    else:
        print("All directories already exist.")

    if kept:
        print(f"Created .gitkeep files:")
        for f in kept:
            print(f"  - {f}")

    print("Project structure setup complete.")


if __name__ == "__main__":
    main()
