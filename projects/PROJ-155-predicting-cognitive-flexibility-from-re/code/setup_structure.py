"""
Script to ensure the project directory structure exists as per plan.md.
Run this once to initialize the folder hierarchy.
"""
import os
import sys

def ensure_dir(path: str) -> None:
    """Create directory if it does not exist."""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")
    else:
        # print(f"Directory already exists: {path}")
        pass

def main():
    """Create the standard project structure."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Core directories per plan.md
    dirs = [
        os.path.join(root, "code"),
        os.path.join(root, "data"),
        os.path.join(root, "docs"),
        os.path.join(root, "tests"),
        # Subdirectories for organization
        os.path.join(root, "data", "raw"),
        os.path.join(root, "data", "processed"),
        os.path.join(root, "data", "results"),
        os.path.join(root, "code", "data"),
        os.path.join(root, "code", "features"),
        os.path.join(root, "code", "analysis"),
        os.path.join(root, "code", "utils"),
        os.path.join(root, "tests", "integration"),
        os.path.join(root, "tests", "unit"),
    ]

    print(f"Ensuring project structure in: {root}")
    for d in dirs:
        ensure_dir(d)
    
    # Create __init__.py files to make them packages
    init_files = [
        os.path.join(root, "code", "__init__.py"),
        os.path.join(root, "code", "data", "__init__.py"),
        os.path.join(root, "code", "features", "__init__.py"),
        os.path.join(root, "code", "analysis", "__init__.py"),
        os.path.join(root, "code", "utils", "__init__.py"),
        os.path.join(root, "data", "__init__.py"),
        os.path.join(root, "docs", "__init__.py"),
        os.path.join(root, "tests", "__init__.py"),
    ]

    for f in init_files:
        if not os.path.exists(f):
            with open(f, 'w') as fh:
                fh.write('"""Auto-generated init file."""\n')
            print(f"Created package marker: {f}")

    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()