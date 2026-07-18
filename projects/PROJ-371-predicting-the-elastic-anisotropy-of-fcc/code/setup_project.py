"""
Script to initialize the project directory structure for PROJ-371.
This script creates the necessary folders for source code, tests, data, and outputs
as defined in the implementation plan.
"""
import os
from pathlib import Path

def main():
    # Define the project root (assuming this script is run from the root)
    # If run as 'python code/setup_project.py', we need to handle the relative path correctly.
    # However, standard practice is to run from root or adjust paths.
    # We will create paths relative to the current working directory.
    base_dir = Path.cwd()

    # Define the directory structure to create
    # Based on T001: src/{data,models,utils,cli} tests/{unit,integration} data/{raw,processed} output
    # Adjusted to match existing API surface which uses 'code/' as root for src/tests
    # The existing API surface shows paths like 'code/src/cli/run_pipeline.py'
    # So the root structure is: code/src/..., code/tests/..., code/data/..., code/output/
    
    # Let's verify the existing file paths in the prompt:
    # code/src/cli/run_pipeline.py
    # code/tests/unit/test_config.py
    # This implies the project root is the parent of 'code'.
    # So we create directories under 'code/'.
    
    project_root = base_dir / "code"
    
    directories = [
        # Source code structure
        project_root / "src" / "data",
        project_root / "src" / "models",
        project_root / "src" / "utils",
        project_root / "src" / "cli",
        
        # Test structure
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
        
        # Data structure
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        
        # Output structure
        project_root / "output",
    ]

    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path.relative_to(base_dir)}")
            created_count += 1
        else:
            print(f"Directory exists: {dir_path.relative_to(base_dir)}")
    
    # Create __init__.py files to make them proper Python packages
    # This is crucial for the imports (e.g., from src.utils.config import ...) to work
    init_files = [
        project_root / "src" / "__init__.py",
        project_root / "src" / "data" / "__init__.py",
        project_root / "src" / "models" / "__init__.py",
        project_root / "src" / "utils" / "__init__.py",
        project_root / "src" / "cli" / "__init__.py",
        project_root / "tests" / "__init__.py",
        project_root / "tests" / "unit" / "__init__.py",
        project_root / "tests" / "integration" / "__init__.py",
    ]

    for init_file in init_files:
        if not init_file.exists():
            init_file.touch()
            print(f"Created package marker: {init_file.relative_to(base_dir)}")
        else:
            print(f"Package marker exists: {init_file.relative_to(base_dir)}")

    # Create .gitkeep files in data directories to ensure they are tracked by git
    # even if they are empty
    gitkeep_files = [
        project_root / "data" / "raw" / ".gitkeep",
        project_root / "data" / "processed" / ".gitkeep",
        project_root / "output" / ".gitkeep",
    ]

    for gitkeep in gitkeep_files:
        if not gitkeep.exists():
            gitkeep.touch()
            print(f"Created .gitkeep: {gitkeep.relative_to(base_dir)}")
        else:
            print(f".gitkeep exists: {gitkeep.relative_to(base_dir)}")

    print("\nProject structure initialization complete.")
    print(f"Created {created_count} new directories.")

if __name__ == "__main__":
    main()