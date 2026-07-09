"""
Script to initialize the project directory structure for llmXive PROJ-011.
Creates required data, state, and reporting directories as specified in T007.
"""
import os
from pathlib import Path

def main():
    """Create the standard directory structure for the project."""
    # Define the project root (assumes this script is in code/ or code/setup/)
    # We use the parent of the current file's directory to find the project root
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent

    # Define the directories to create based on T007 and T001 specs
    # T007 specifically asks for: data/ (raw, processed, models) and state/
    # T001 asks for: data/raw, data/processed, data/models, code/preprocessing, code/modeling, code/analysis, code/utils, code/reporting, tests/unit, tests/integration, tests/contract, state, docs
    
    # We will ensure the specific T007 requirements are met, along with the T001 foundation
    dirs_to_create = [
        # Data structure (T007)
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "models",
        project_root / "data" / "reports", # Added for T018b, T038a
        
        # State structure (T007)
        project_root / "state",
        
        # Additional T001 structure to ensure completeness if not already done
        project_root / "code" / "preprocessing",
        project_root / "code" / "modeling",
        project_root / "code" / "analysis",
        project_root / "code" / "utils",
        project_root / "code" / "reporting",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
        project_root / "tests" / "contract",
        project_root / "docs",
    ]

    created_count = 0
    for dir_path in dirs_to_create:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path.relative_to(project_root)}")
            created_count += 1
        else:
            # Check if it's a directory, if it's a file, that's an error
            if not dir_path.is_dir():
                print(f"Warning: Path exists but is not a directory: {dir_path.relative_to(project_root)}")
            else:
                print(f"Directory already exists: {dir_path.relative_to(project_root)}")

    # Initialize __init__.py files in code/ and tests/ packages if they don't exist
    # This satisfies the "initialize __init__.py files" part of T001
    init_files = [
        project_root / "code" / "__init__.py",
        project_root / "code" / "preprocessing" / "__init__.py",
        project_root / "code" / "modeling" / "__init__.py",
        project_root / "code" / "analysis" / "__init__.py",
        project_root / "code" / "utils" / "__init__.py",
        project_root / "code" / "reporting" / "__init__.py",
        project_root / "tests" / "__init__.py",
        project_root / "tests" / "unit" / "__init__.py",
        project_root / "tests" / "integration" / "__init__.py",
        project_root / "tests" / "contract" / "__init__.py",
    ]

    for init_file in init_files:
        if not init_file.exists():
            init_file.touch()
            print(f"Created empty __init__.py: {init_file.relative_to(project_root)}")
        else:
            print(f"__init__.py already exists: {init_file.relative_to(project_root)}")

    # Create a placeholder .gitkeep in data directories to ensure they are tracked by git
    # (optional but good practice for empty directories in git)
    data_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "models",
        project_root / "data" / "reports",
    ]
    for d in data_dirs:
        gitkeep = d / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()

    print(f"\nSetup complete. Created {created_count} new directories.")

if __name__ == "__main__":
    main()