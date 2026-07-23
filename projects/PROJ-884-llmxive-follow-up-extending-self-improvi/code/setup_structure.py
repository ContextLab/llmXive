import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure for PROJ-884-llmxive-follow-up-extending-self-improvi.
    This script executes the mkdir -p logic specified in T001a.
    """
    project_root = Path("projects/PROJ-884-llmxive-follow-up-extending-self-improvi")
    
    # Define the directory structure based on the task requirement
    # mkdir -p projects/PROJ-884-llmxive-follow-up-extending-self-improvi/{data/raw,data/processed,code/{dataset,symbolic,bes,analysis,utils},tests/{unit,integration}}
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "code" / "dataset",
        project_root / "code" / "symbolic",
        project_root / "code" / "bes",
        project_root / "code" / "analysis",
        project_root / "code" / "utils",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
    ]

    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    # Create __init__.py files to ensure these are recognized as packages
    init_files = []
    for dir_path in directories:
        init_file = dir_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            init_files.append(init_file)
            print(f"Created __init__.py: {init_file}")

    print(f"\nProject structure initialized successfully.")
    print(f"Created {created_count} new directories.")
    print(f"Created {len(init_files)} new __init__.py files.")
    
    # List the created structure for verification
    print("\nDirectory structure:")
    for dir_path in sorted(directories):
        if dir_path.exists():
            print(f"  [DIR] {dir_path.relative_to(project_root.parent) if project_root.parent in dir_path.parents else dir_path}")

    return 0

if __name__ == "__main__":
    sys.exit(main())