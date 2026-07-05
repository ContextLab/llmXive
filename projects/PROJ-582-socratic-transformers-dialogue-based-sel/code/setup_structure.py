"""
Script to initialize the project directory structure as per T001.
"""
import os
import sys

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define directories to create
    directories = [
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
    
    created_dirs = []
    for d in directories:
        full_path = os.path.join(base_dir, d)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            created_dirs.append(d)
        else:
            # Ensure it is a directory, not a file
            if not os.path.isdir(full_path):
                print(f"Error: {d} exists but is not a directory.")
                sys.exit(1)
    
    if created_dirs:
        print(f"Created directories: {', '.join(created_dirs)}")
    else:
        print("All directories already exist.")
    
    # Verify __init__.py files exist in src and tests root
    init_files = [
        os.path.join(base_dir, "src", "__init__.py"),
        os.path.join(base_dir, "tests", "__init__.py"),
    ]
    
    for init_file in init_files:
        if not os.path.exists(init_file):
            print(f"Warning: {init_file} does not exist. Please ensure it was created manually or by the artifact writer.")
        else:
            print(f"Verified: {init_file} exists.")

    # Verify requirements.txt exists
    req_file = os.path.join(base_dir, "requirements.txt")
    if not os.path.exists(req_file):
        print(f"Warning: {req_file} does not exist. Please ensure it was created manually or by the artifact writer.")
    else:
        print(f"Verified: {req_file} exists.")

if __name__ == "__main__":
    main()