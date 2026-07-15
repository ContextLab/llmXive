"""
Setup script to initialize the project directory structure for the
'Impact of Visual Complexity on Cognitive Load' research pipeline.

This script creates the required folders under 'code/' as specified in T001a:
- code/src/lib/
- code/src/metrics/
- code/src/experiment/
- code/src/analysis/
- code/tests/

It also ensures __init__.py files are present to make them Python packages.
"""
import os
from pathlib import Path

# Define the project root relative to this script (assuming script is in code/)
# The task description implies paths relative to the project root, but the
# constraint says "All artifact paths are relative to the project root".
# However, standard practice for a "code directory structure" task usually
# implies creating the structure where the code lives.
# Based on the task description: "Create code directory structure (`src/lib/`...)"
# and the constraint "Stay inside the project tree... under `code/`",
# we will create the structure at `code/src/...` and `code/tests/`.

BASE_DIR = Path(__file__).parent.resolve()

# Define the directories to create
# Note: The task asks for `src/`, `tests/` at repository root in the path conventions,
# but the task T001a specifically says "Create code directory structure".
# Given the constraint "Stay inside the project tree... under `code/`",
# we will create the structure inside `code/`.
# If the project root is the repo root, and `code/` is a subfolder, then:
# `code/src/lib`, `code/src/metrics`, etc.

dirs_to_create = [
    BASE_DIR / "src" / "lib",
    BASE_DIR / "src" / "metrics",
    BASE_DIR / "src" / "experiment",
    BASE_DIR / "src" / "analysis",
    BASE_DIR / "tests",
]

def ensure_directory(path: Path) -> None:
    """Creates the directory and an __init__.py if it's a Python package."""
    path.mkdir(parents=True, exist_ok=True)
    
    # Add __init__.py for Python packages
    if path.name == "lib" or path.name == "metrics" or \
       path.name == "experiment" or path.name == "analysis" or \
       path.name == "tests":
        init_file = path / "__init__.py"
        if not init_file.exists():
            init_file.write_text("# Auto-generated package init\n")
            print(f"Created package init: {init_file}")
    
    print(f"Ensured directory: {path}")

def main():
    print(f"Initializing project structure at: {BASE_DIR}")
    for dir_path in dirs_to_create:
        ensure_directory(dir_path)
    print("Directory structure setup complete.")

if __name__ == "__main__":
    main()