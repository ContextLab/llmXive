"""
Script to initialize the project directory structure for T001.
Running this script ensures all required directories and __init__.py files exist.
"""
import os
import sys

def create_project_structure():
    """
    Creates the required directory structure and initializes __init__.py files.
    Paths are relative to the project root.
    """
    # Define the root directory (assumed to be where this script is run from)
    # In the context of the pipeline, this script is run from the project root.
    base_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(base_dir)

    # Define the directory structure to create
    # All paths are relative to the project root (parent_dir)
    directories = [
        "code",
        "code/utils",
        "code/pipeline",
        "code/results",
        "code/schemas",
        "data",
        "data/raw",
        "data/processed",
        "results",
        "specs",
        "tests",
        "tests/unit",
        "tests/integration",
    ]

    created_count = 0
    init_count = 0

    print(f"Initializing project structure in: {parent_dir}")

    for dir_path in directories:
        full_path = os.path.join(parent_dir, dir_path)
        
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            created_count += 1
            print(f"  Created directory: {dir_path}")
        else:
            print(f"  Directory exists: {dir_path}")

        # Create __init__.py if it doesn't exist
        init_file = os.path.join(full_path, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w", encoding="utf-8") as f:
                # Add a simple comment based on the directory purpose
                if "code" in dir_path:
                    f.write(f"# {' '.join(dir_path.split('/'))} package\n")
                elif "data" in dir_path:
                    f.write(f"# {' '.join(dir_path.split('/'))} storage\n")
                elif "tests" in dir_path:
                    f.write(f"# {' '.join(dir_path.split('/'))} package\n")
                elif "results" in dir_path:
                    f.write(f"# {' '.join(dir_path.split('/'))} output package\n")
                elif "specs" in dir_path:
                    f.write(f"# {' '.join(dir_path.split('/'))} package\n")
                else:
                    f.write(f"# {' '.join(dir_path.split('/'))} package\n")
            init_count += 1
            print(f"  Initialized: {dir_path}/__init__.py")
        else:
            print(f"  Init file exists: {dir_path}/__init__.py")

    print(f"\nProject structure initialization complete.")
    print(f"  Directories created: {created_count}")
    print(f"  __init__.py files created: {init_count}")
    
    # Verify structure
    print("\nVerifying structure...")
    missing = []
    for dir_path in directories:
        full_path = os.path.join(parent_dir, dir_path)
        if not os.path.isdir(full_path):
            missing.append(dir_path)
        
        init_file = os.path.join(full_path, "__init__.py")
        if not os.path.isfile(init_file):
            missing.append(f"{dir_path}/__init__.py")

    if missing:
        print(f"  ERROR: Missing items: {missing}")
        return False
    else:
        print("  Verification passed: All directories and init files present.")
        return True

if __name__ == "__main__":
    success = create_project_structure()
    sys.exit(0 if success else 1)