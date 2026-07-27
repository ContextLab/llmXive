"""
Setup script to initialize the project directory structure.
Creates required directories and placeholder files as per T001.
"""
import os
import sys
from pathlib import Path

def main():
    base_dir = Path(__file__).parent
    project_root = base_dir / "projects" / "PROJ-582-socratic-transformers-dialogue-based-sel" / "code"
    
    # Define directories to create
    dirs_to_create = [
        project_root / "src" / "data",
        project_root / "src" / "train",
        project_root / "src" / "eval",
        project_root / "src" / "analyze",
        project_root / "src" / "utils",
        project_root / "tests",
        project_root / "tests" / "contract",
        project_root / "tests" / "integration",
        # Data sub-structure for T004 (created here to ensure structure exists)
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "results",
    ]

    # Define files to create (if they don't exist or are empty)
    files_to_create = [
        project_root / "src" / "__init__.py",
        project_root / "tests" / "__init__.py",
        project_root / "src" / "data" / "__init__.py",
        project_root / "src" / "train" / "__init__.py",
        project_root / "src" / "eval" / "__init__.py",
        project_root / "src" / "analyze" / "__init__.py",
        project_root / "src" / "utils" / "__init__.py",
        project_root / "tests" / "contract" / "__init__.py",
        project_root / "tests" / "integration" / "__init__.py",
        project_root / "data" / "raw" / ".gitkeep",
        project_root / "data" / "processed" / ".gitkeep",
        project_root / "data" / "results" / ".gitkeep",
    ]

    print(f"Setting up project structure at: {project_root}")

    # Create directories
    for d in dirs_to_create:
        d.mkdir(parents=True, exist_ok=True)
        print(f"  Created directory: {d.relative_to(project_root)}")

    # Create files
    for f in files_to_create:
        if not f.exists():
            f.touch()
            print(f"  Created file: {f.relative_to(project_root)}")
        else:
            print(f"  Skipped existing file: {f.relative_to(project_root)}")

    print("Project structure setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())