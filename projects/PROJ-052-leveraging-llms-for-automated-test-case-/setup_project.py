"""
Script to initialize the project directory structure for T001.
Creates required directories and empty __init__.py files.
"""
import os
import sys

def main():
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Define directories to create
    directories = [
        "code",
        "specs",
        "data",
        "contracts",
        "tests/unit",
        "tests/integration"
    ]
    
    # Define paths for __init__.py files
    init_paths = [
        "code/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py"
    ]
    
    created_dirs = []
    created_files = []
    
    # Create directories
    for dir_path in directories:
        full_path = os.path.join(project_root, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            created_dirs.append(dir_path)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")
    
    # Create __init__.py files
    for file_path in init_paths:
        full_path = os.path.join(project_root, file_path)
        if not os.path.exists(full_path):
            # Ensure parent directory exists
            parent_dir = os.path.dirname(full_path)
            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir)
            
            with open(full_path, 'w') as f:
                # Write minimal content to make it a valid Python module
                if "tests" in file_path:
                    f.write("# Test suite for llmXive\n")
                else:
                    f.write("# llmXive: Automated Test Case Generation\n")
            
            created_files.append(file_path)
            print(f"Created file: {file_path}")
        else:
            print(f"File already exists: {file_path}")
    
    print(f"\nSetup complete. Created {len(created_dirs)} directories and {len(created_files)} __init__.py files.")
    return 0

if __name__ == "__main__":
    sys.exit(main())