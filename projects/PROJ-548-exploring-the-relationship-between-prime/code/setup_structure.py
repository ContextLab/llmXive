import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure as defined in T001.
    """
    # Define the project root (relative to this script's location)
    # The script is at code/setup_structure.py
    project_root = Path(__file__).parent.parent

    # Define the directory structure relative to project_root
    # Note: The task description lists paths like 'src/data/', 'tests/unit/'
    # Assuming these are relative to the project root.
    # However, looking at the existing API surface, files are at 'code/src/...'
    # and 'code/tests/...'.
    # The task description says: "Create project structure per implementation plan:
    # `src/data/`, `src/analysis/`, `src/utils/`, `src/cli/`, `tests/unit/`, `tests/integration/`,
    # `data/raw/`, `data/processed/`, `data/results/`, `results/`, `state/`"
    #
    # Given the existing files are in `code/src/...` and `code/tests/...`,
    # it is highly likely the "project root" for this structure is the `code/` directory
    # or the task description implies the structure *inside* the `code/` directory.
    #
    # Let's assume the task wants the structure relative to the `code/` directory
    # because the existing files (e.g., `code/src/data/generate_primes.py`) already
    # exist in that hierarchy.
    #
    # If we create `src/` at the root of the repo (parent of `code/`), it would conflict
    # or be separate from the existing `code/src/`.
    #
    # Re-reading the task: "Create project structure per implementation plan: `src/data/`..."
    # And the existing files are in `code/src/...`.
    # It is most logical that the task intends to ensure the directories *within* `code/`
    # exist, or that the `code/` directory IS the project root for this specific project
    # implementation.
    #
    # Let's assume the base directory is `code/` (where this script is located).
    base_dir = project_root / "code"

    # Directories to create
    directories = [
        "src/data",
        "src/analysis",
        "src/utils",
        "src/cli",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/processed",
        "data/results",
        "results",
        "state",
    ]

    created_count = 0
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            # Ensure it's a directory
            if not full_path.is_dir():
                print(f"Warning: {full_path} exists but is not a directory.")
            else:
                print(f"Directory already exists: {full_path}")

    # Create __init__.py files to make them Python packages where appropriate
    # src subdirectories
    src_subdirs = ["data", "analysis", "utils", "cli"]
    for subdir in src_subdirs:
        init_file = base_dir / "src" / subdir / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"Created: {init_file}")

    # tests subdirectories
    test_subdirs = ["unit", "integration"]
    for subdir in test_subdirs:
        init_file = base_dir / "tests" / subdir / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"Created: {init_file}")
    
    # tests root
    tests_root_init = base_dir / "tests" / "__init__.py"
    if not tests_root_init.exists():
        tests_root_init.touch()
        print(f"Created: {tests_root_init}")
    
    # src root
    src_root_init = base_dir / "src" / "__init__.py"
    if not src_root_init.exists():
        src_root_init.touch()
        print(f"Created: {src_root_init}")

    # data subdirectories (raw, processed, results)
    data_subdirs = ["raw", "processed", "results"]
    for subdir in data_subdirs:
        init_file = base_dir / "data" / subdir / ".gitkeep"
        if not init_file.exists():
            init_file.touch()
            print(f"Created: {init_file}")
    
    # data root init (optional, but good for package structure if needed)
    # data_root_init = base_dir / "data" / "__init__.py"
    # if not data_root_init.exists():
    #     data_root_init.touch()
    
    # results and state
    results_dir = base_dir / "results"
    if not (results_dir / ".gitkeep").exists():
        (results_dir / ".gitkeep").touch()
        print(f"Created: {results_dir}/.gitkeep")
    
    state_dir = base_dir / "state"
    if not (state_dir / ".gitkeep").exists():
        (state_dir / ".gitkeep").touch()
        print(f"Created: {state_dir}/.gitkeep")

    print(f"\nSetup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())