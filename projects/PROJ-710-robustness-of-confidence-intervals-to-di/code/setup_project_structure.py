"""
Project Structure Setup Script for PROJ-710.
Creates the required directory hierarchy for the research pipeline.
"""
import os
from pathlib import Path

def main():
    # Define the project root relative to the script location or current working directory
    # The task specifies paths relative to the project root.
    # We assume the script is run from the project root or the code directory.
    # To be safe, we resolve relative to the script's parent (code/) then go up one level?
    # Actually, the task says: "All artifact paths are relative to the project root"
    # and "Create project directory structure: projects/PROJ-710-.../..."
    # However, the existing API surface shows files in `code/`, `tests/`, etc. at the root of the project context provided.
    # The task description lists paths like `projects/PROJ-710-.../code/`.
    # But the "Existing project API surface" shows `code/config.py`, `code/main.py`, etc.
    # This implies the current working directory IS the project root for the purpose of the code structure,
    # or the `projects/PROJ-710...` part was the conceptual folder name and the actual structure is flattened into `code/`, `data/`, etc.
    # Given the constraint "Stay inside the project tree" and the existing files are in `code/`, `tests/`, `data/` directly under the root,
    # we will create the directories that match the existing file structure (code/, data/, analysis/, utils/, tests/, artifacts/).
    # The task description's `projects/PROJ-710...` prefix likely refers to the repository root if it were a monorepo,
    # but since we are implementing inside the existing `code/` structure, we create the subdirectories relative to the root.

    # Required directories based on task T001a description, mapped to the existing project root structure:
    # The task asks for:
    # projects/PROJ-710-.../code/ -> exists as code/
    # projects/PROJ-710-.../code/data/ -> needs code/data/
    # projects/PROJ-710-.../code/analysis/ -> needs code/analysis/
    # projects/PROJ-710-.../code/utils/ -> needs code/utils/
    # projects/PROJ-710-.../code/tests/ -> needs code/tests/
    # projects/PROJ-710-.../artifacts/ -> needs artifacts/

    base_dirs = [
        "code/data",
        "code/analysis",
        "code/utils",
        "code/tests",
        "artifacts"
    ]

    created = []
    for dir_path in base_dirs:
        path = Path(dir_path)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(str(path))
            print(f"Created directory: {path}")
        else:
            print(f"Directory already exists: {path}")

    # Create __init__.py files to ensure they are recognized as packages
    # The task T001b is marked completed, but this script ensures structure validity.
    # We will create them if missing to ensure the structure is robust.
    init_files = [
        "code/__init__.py",
        "code/data/__init__.py",
        "code/analysis/__init__.py",
        "code/utils/__init__.py",
        "code/tests/__init__.py"
    ]

    for init_file in init_files:
        path = Path(init_file)
        if not path.exists():
            path.touch()
            created.append(str(path))
            print(f"Created file: {path}")
        else:
            print(f"File already exists: {path}")

    if not created:
        print("No new directories or files were created. Structure is already complete.")
    else:
        print(f"Successfully created {len(created)} items.")

if __name__ == "__main__":
    main()