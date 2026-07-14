"""
Script to initialize the project directory structure and Python packages.
This implements Task T001.
"""
import os
import sys

def create_directories():
    """Create the required directory structure."""
    # Define the root directory (current working directory or specified path)
    # For this task, we assume running from the project root
    base_dirs = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "data/results",
        "docs"
    ]
    
    # Define the package directories that need __init__.py
    package_dirs = [
        "code",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract"
    ]

    created_dirs = []
    created_files = []

    # Create base directories
    for dir_path in base_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            created_dirs.append(dir_path)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")

    # Create __init__.py files in package directories
    for pkg_dir in package_dirs:
        init_path = os.path.join(pkg_dir, "__init__.py")
        if not os.path.exists(init_path):
            with open(init_path, "w") as f:
                f.write('"""\n')
                f.write(f'{pkg_dir.replace("/", ".")} package\n')
                f.write('"""\n')
            created_files.append(init_path)
            print(f"Created file: {init_path}")
        else:
            print(f"File already exists: {init_path}")

    return created_dirs, created_files

def main():
    print("Initializing project structure for Task T001...")
    dirs, files = create_directories()
    print(f"\nSummary:")
    print(f"  Directories created: {len(dirs)}")
    print(f"  Files created: {len(files)}")
    
    if not dirs and not files:
        print("  No changes made (structure already exists).")
    else:
        print("  Project structure initialized successfully.")

if __name__ == "__main__":
    main()