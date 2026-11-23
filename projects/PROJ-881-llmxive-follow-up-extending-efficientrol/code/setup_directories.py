"""
Setup script to create the project directory structure for llmXive Follow-up.
Creates all required directories under the project root.
"""
import os
import sys
from pathlib import Path


def main():
    """Create the project directory structure."""
    # Define the project root relative to the script location or current working directory
    # Assuming the script is run from the project root or code/ directory
    # We will construct paths relative to the current working directory
    cwd = Path.cwd()

    # Define base paths
    project_root = cwd / "projects" / "PROJ-881-llmxive-follow-up-extending-efficientrol" / "code"
    specs_root = cwd / "specs" / "001-entropy-validity-prediction"

    # Directories to create under code/
    code_dirs = [
        "src",
        "tests",
        "data",
        "docs",
        "scripts",
        "results",
        # Additional standard directories often needed
        "logs",
        "config",
        "utils", # Will be populated by src/utils structure
        "generation", # src/generation
        "analysis", # src/analysis
        "data", # src/data (already listed, but ensuring structure)
    ]

    # Directories to create under specs/
    specs_dirs = [
        "contracts",
    ]

    # Create code directories
    for dir_name in code_dirs:
        dir_path = project_root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

        # Create __init__.py for src subdirectories to make them packages
        if dir_name.startswith("src"):
            # Create sub-package init files if they don't exist
            # Note: The task specifically asks for top-level dirs, but making them packages is good practice
            # We will create __init__.py in the root of src if it's not there, 
            # and potentially in subdirs if we created them as subdirs.
            # The task list implies flat structure under code/src/, code/tests/ etc.
            # Let's ensure the root src, tests, etc are recognized as packages if needed, 
            # but primarily we just need the directories.
            pass

    # Create specs directories
    for dir_name in specs_dirs:
        dir_path = specs_root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

    print("\nDirectory structure creation complete.")
    print(f"Project root: {project_root}")
    print(f"Specs root: {specs_root}")


if __name__ == "__main__":
    main()