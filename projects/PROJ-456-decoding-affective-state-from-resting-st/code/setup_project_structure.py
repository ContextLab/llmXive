import os
import sys
from pathlib import Path

def create_directory_structure(base_dir: Path) -> None:
    """
    Create the project directory structure for PROJ-456.
    
    Required structure:
    projects/PROJ-456-decoding-affective-state-from-resting-st/
        ├── code/
        ├── data/
        │   ├── raw/
        │   ├── processed/
        │   ├── templates/
        │   └── logs/
        ├── tests/
        │   └── unit/
        ├── docs/
        └── state/
    """
    project_root = base_dir / "projects" / "PROJ-456-decoding-affective-state-from-resting-st"
    
    # Define all required directories
    directories = [
        project_root,
        project_root / "code",
        project_root / "data",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "templates",
        project_root / "data" / "logs",
        project_root / "tests",
        project_root / "tests" / "unit",
        project_root / "docs",
        project_root / "state",
    ]
    
    # Create directories
    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path.relative_to(base_dir)}")
    
    # Create .gitkeep files to ensure directories are tracked by git
    for dir_path in directories:
        gitkeep = dir_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("# Keep this directory in git\n")
    
    print(f"\nProject structure created successfully at: {project_root}")

def create_placeholder_files(base_dir: Path) -> None:
    """
    Create essential placeholder files for the project.
    """
    project_root = base_dir / "projects" / "PROJ-456-decoding-affective-state-from-resting-st"
    
    # Create README.md
    readme_content = """# Decoding Affective State from Resting-State EEG Microstates

## Project Overview
This project implements an automated pipeline for decoding affective states from resting-state EEG microstate analysis.

## Directory Structure
- `code/`: Source code for the pipeline
- `data/`: Data storage (raw, processed, templates, logs)
- `tests/`: Unit and integration tests
- `docs/`: Documentation
- `state/`: Pipeline state and metadata

## Prerequisites
- Python 3.8+
- mne (CPU-only)
- numpy
- scipy

## Execution
Run the pipeline using the main entry point scripts in `code/`.
"""
    (project_root / "README.md").write_text(readme_content)
    
    # Create requirements.txt
    requirements_content = """numpy>=1.21.0
scipy>=1.7.0
mne>=1.0.0
pandas>=1.3.0
scikit-learn>=1.0.0
"""
    (project_root / "requirements.txt").write_text(requirements_content)
    
    # Create __init__.py files
    (project_root / "code" / "__init__.py").write_text("# Code package\n")
    (project_root / "tests" / "__init__.py").write_text("# Tests package\n")
    (project_root / "tests" / "unit" / "__init__.py").write_text("# Unit tests package\n")
    
    print("Placeholder files created successfully.")

def main():
    """
    Main entry point for project structure setup.
    """
    # Determine base directory (current working directory)
    base_dir = Path.cwd()
    
    print("Starting project structure creation...")
    create_directory_structure(base_dir)
    create_placeholder_files(base_dir)
    print("\nSetup complete!")

if __name__ == "__main__":
    main()