"""
Script to initialize the project directory structure and create necessary __init__.py files.
This script corresponds to task T001.
"""
import os
from pathlib import Path

def main():
    # Define the root directory (current working directory)
    root = Path.cwd()

    # Define the directories to create based on the task description
    # Note: The task asks for 'src', but the API surface shows 'code/' as the project root.
    # We will create 'code/src', 'code/data', etc., to align with the project's path conventions
    # while respecting the task's intent to create the internal structure.
    # However, looking at the task description: "Execute `mkdir -p src data/raw ...`"
    # And the constraint: "All artifact paths are relative to the project root and MUST live under `code/`..."
    # The task description seems to assume the project root IS the repo root.
    # But the API surface provided uses `code/` as the root for artifacts.
    # To be safe and compliant with the "Stay inside the project tree" constraint which says
    # "MUST live under `code/`", I will create the structure relative to `code/`.
    # Wait, the task says "Create project structure...". If I run this from the repo root,
    # it creates `src`, `data`, etc.
    # Let's look at the API surface again. `code/setup_project.py` exists.
    # The prompt says: "All artifact paths are relative to the project root and MUST live under `code/`".
    # This implies the "project root" for the LLM is the `code/` directory?
    # No, usually "project root" is where the repo is. The constraint says artifacts MUST be under `code/`.
    # So I should create `code/src`, `code/data`, etc.
    # But the task description explicitly says `mkdir -p src data/raw...`.
    # If I run the script from the repo root, it creates `src` in the repo root.
    # This violates the "MUST live under `code/`" constraint if the repo root is the project root.
    # Let's assume the "project root" for the purpose of this task is the directory where `code/` lives.
    # The constraint says: "All artifact paths... MUST live under `code/`".
    # So I will create the directories INSIDE `code/`.
    # The task description might be generic. I will adapt to the specific project constraint.
    # Target directories:
    # code/src
    # code/data/raw
    # code/data/processed
    # code/tests/unit
    # code/tests/integration
    # code/docs

    base_path = Path("code")
    
    # Ensure base path exists
    base_path.mkdir(exist_ok=True)

    directories = [
        base_path / "src",
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "tests" / "unit",
        base_path / "tests" / "integration",
        base_path / "docs",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

    # Create __init__.py files
    init_files = [
        base_path / "src" / "__init__.py",
        base_path / "tests" / "__init__.py",
        base_path / "tests" / "unit" / "__init__.py",
        base_path / "tests" / "integration" / "__init__.py",
    ]

    for init_file in init_files:
        init_file.touch(exist_ok=True)
        print(f"Created empty file: {init_file}")

    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()
