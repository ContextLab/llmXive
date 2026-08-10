"""
Script to initialize the directory structure for the Socratic Transformers project.
This script creates the necessary folders and placeholder files as defined in T001.
"""
import os
from pathlib import Path

def main():
    project_root = Path(__file__).parent
    base_dirs = [
        "src",
        "src/data",
        "src/train",
        "src/eval",
        "src/analyze",
        "src/utils",
        "tests",
        "tests/contract",
        "tests/integration",
    ]

    print(f"Setting up project structure in: {project_root}")

    for dir_path in base_dirs:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"  Created directory: {full_path}")

    # Ensure __init__.py files exist in src and tests root
    src_init = project_root / "src" / "__init__.py"
    if not src_init.exists():
        src_init.write_text('"""Core source package."""\n')
        print(f"  Created: {src_init}")

    tests_init = project_root / "tests" / "__init__.py"
    if not tests_init.exists():
        tests_init.write_text('"""Test suite."""\n')
        print(f"  Created: {tests_init}")

    print("Project structure setup complete.")

if __name__ == "__main__":
    main()