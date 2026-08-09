import os
import sys
from pathlib import Path

def create_directory_structure(root_dir: Path) -> None:
    """
    Create the required project directory structure for the llmXive pipeline.
    
    Creates:
    - code/ (source code)
    - code/src/ (internal modules)
    - code/src/data/ (data loading and processing)
    - code/src/utils/ (utilities)
    - code/src/analysis/ (analysis modules)
    - code/src/viz/ (visualization modules)
    - tests/ (test suite)
    - tests/unit/ (unit tests)
    - tests/integration/ (integration tests)
    - data/ (raw and processed data)
    - data/raw/ (downloaded raw data)
    - data/processed/ (preprocessed data)
    - results/ (analysis results)
    - results/stats/ (statistical outputs)
    - results/figures/ (visualizations)
    - specs/ (feature specifications)
    """
    directories = [
        "code",
        "code/src",
        "code/src/data",
        "code/src/utils",
        "code/src/analysis",
        "code/src/viz",
        "tests",
        "tests/unit",
        "tests/integration",
        "data",
        "data/raw",
        "data/processed",
        "results",
        "results/stats",
        "results/figures",
        "specs",
    ]
    
    for dir_path in directories:
        full_path = root_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep files to ensure directories are tracked by git
        gitkeep = full_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
    
    print(f"Created directory structure at {root_dir}")
    for dir_path in directories:
        print(f"  - {dir_path}")

def create_initial_files(root_dir: Path) -> None:
    """
    Create initial placeholder files for the project structure.
    """
    # Create __init__.py files for Python packages
    init_files = [
        "code/src/__init__.py",
        "code/src/data/__init__.py",
        "code/src/utils/__init__.py",
        "code/src/analysis/__init__.py",
        "code/src/viz/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py",
    ]
    
    for file_path in init_files:
        full_path = root_dir / file_path
        if not full_path.exists():
            full_path.touch()
            # Add minimal content to make it a proper package
            with open(full_path, 'w') as f:
                f.write(f'"""{file_path.replace("/", ".")} package."""\n')
    
    print("Created initial package files")

def main():
    """Main entry point for project setup."""
    # Determine project root (parent of code/)
    # We assume this script is run from the project root
    root_dir = Path.cwd()
    
    print(f"Setting up project structure at: {root_dir}")
    
    create_directory_structure(root_dir)
    create_initial_files(root_dir)
    
    print("\nProject structure setup complete!")
    print("Next steps:")
    print("  1. Verify directory structure with: ls -R")
    print("  2. Initialize git repository if not already done")
    print("  3. Install dependencies: pip install -r requirements.txt")

if __name__ == "__main__":
    main()
