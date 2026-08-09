"""
Script to create the required directory structure for PROJ-294.
This satisfies T001a (Create directory structure) and T001b (Create __init__.py files).
"""
import os
import sys

# Define the base project directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_NAME = "PROJ-294-evaluating-the-impact-of-code-generation"
BASE_DIR = os.path.join(PROJECT_ROOT, "projects", PROJECT_NAME)

# Define the required directory structure
DIR_STRUCTURE = [
    "code",
    "data",
    "state",
    "results",
    "tests",
    "docs",
    "tests/unit",
    "tests/integration",
]

# Define the required __init__.py locations
INIT_FILES = [
    "code/__init__.py",
    "tests/__init__.py",
    "tests/unit/__init__.py",
    "tests/integration/__init__.py",
]

def ensure_directory(path):
    """Create directory if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def create_init_file(path):
    """Create an empty __init__.py file if it doesn't exist."""
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write("# Package initialization\n")
        print(f"Created __init__.py: {path}")
    else:
        print(f"__init__.py already exists: {path}")

def main():
    print(f"Setting up project structure in: {BASE_DIR}")
    
    # Create base directory
    ensure_directory(BASE_DIR)
    
    # Create subdirectories
    for dir_path in DIR_STRUCTURE:
        full_path = os.path.join(BASE_DIR, dir_path)
        ensure_directory(full_path)
    
    # Create __init__.py files
    for init_path in INIT_FILES:
        full_path = os.path.join(BASE_DIR, init_path)
        create_init_file(full_path)
    
    print("\nProject structure setup complete.")
    print(f"Base directory: {BASE_DIR}")
    
    # Print the final structure for verification
    print("\nFinal directory structure:")
    for root, dirs, files in os.walk(BASE_DIR):
        level = root.replace(BASE_DIR, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            print(f"{subindent}{file}")

if __name__ == "__main__":
    main()