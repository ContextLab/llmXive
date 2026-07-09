"""
Script to initialize the project directory structure and create __init__.py files.
Executes the required directory creation and file generation for T001.
"""
import os
import sys

def main():
    # Define the directory structure relative to the project root
    # The script assumes it is run from the project root or handles relative paths correctly
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Directories to create
    # Based on T001: code/data, code/models, code/analysis, code/utils
    # and data/raw, data/processed, results, tests
    dirs_to_create = [
        os.path.join(base_dir, "code", "data"),
        os.path.join(base_dir, "code", "models"),
        os.path.join(base_dir, "code", "analysis"),
        os.path.join(base_dir, "code", "utils"),
        os.path.join(base_dir, "data", "raw"),
        os.path.join(base_dir, "data", "processed"),
        os.path.join(base_dir, "results"),
        os.path.join(base_dir, "tests"),
    ]

    # Directories under code/ that need __init__.py
    code_subdirs = [
        "data",
        "models",
        "analysis",
        "utils"
    ]

    print("Initializing project structure for PROJ-158...")

    # Create directories
    created_dirs = []
    for dir_path in dirs_to_create:
        if not os.path.exists(dir_path):
          os.makedirs(dir_path)
          created_dirs.append(dir_path)
          print(f"Created directory: {dir_path}")
        else:
          print(f"Directory already exists: {dir_path}")

    # Create __init__.py files in code/ subdirectories
    init_files_created = []
    for subdir in code_subdirs:
        init_path = os.path.join(base_dir, "code", subdir, "__init__.py")
        if not os.path.exists(init_path):
            with open(init_path, "w") as f:
                f.write("# Auto-generated package initialization file for PROJ-158\n")
            init_files_created.append(init_path)
            print(f"Created __init__.py: {init_path}")
        else:
            print(f"__init__.py already exists: {init_path}")

    print("\nProject structure initialization complete.")
    print(f"Created {len(created_dirs)} directories.")
    print(f"Created {len(init_files_created)} __init__.py files.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
