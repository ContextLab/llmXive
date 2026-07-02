import os
import sys

def create_directories():
    """
    Creates the necessary directory structure for the project.
    This function is called by the main entry point to ensure
    data, code, tests, and reports directories exist.
    """
    # Define the project root (assuming script is run from root or code/)
    # We use the directory of this script as the anchor to find the project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    # Directories to create relative to project root
    dirs_to_create = [
        "data/raw",
        "data/interim",
        "data/processed",
        "code/tests",
        "tests/unit",
        "tests/integration",
        "reports"
    ]

    created_count = 0
    for dir_path in dirs_to_create:
        full_path = os.path.join(project_root, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    return created_count

def create_init_files():
    """
    Creates __init__.py files in code/ and tests/ to ensure they are
    treated as Python packages.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    init_paths = [
        "code/__init__.py",
        "code/tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py"
    ]

    created_count = 0
    for init_path in init_paths:
        full_path = os.path.join(project_root, init_path)
        # Ensure parent directory exists before creating __init__.py
        parent_dir = os.path.dirname(full_path)
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)

        if not os.path.exists(full_path):
            with open(full_path, 'w') as f:
                f.write("# Package initialization\n")
            print(f"Created init file: {full_path}")
            created_count += 1
        else:
            print(f"Init file already exists: {full_path}")

    return created_count

def main():
    """
    Main entry point to set up the project directory structure.
    """
    print("Starting directory setup...")
    dir_count = create_directories()
    init_count = create_init_files()
    print(f"Setup complete. Created {dir_count} directories and {init_count} init files.")
    return 0

if __name__ == "__main__":
    sys.exit(main())