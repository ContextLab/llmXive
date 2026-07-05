"""
Script to initialize the project directory structure and __init__.py files.
Implements Task T001a and T001b.
"""
import os
import sys

def ensure_dir(directory):
    """Create directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")
    else:
        print(f"Directory already exists: {directory}")

def create_init_file(path):
    """Create an empty __init__.py file."""
    # Check if file exists to avoid overwriting if user added content
    if not os.path.exists(path):
        with open(path, 'w') as f:
            f.write("# Auto-generated init file\n")
        print(f"Created file: {path}")
    else:
        print(f"File already exists: {path}")

def main():
    # Define base directory (project root)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Define directories to create
    directories = [
        "code",
        "tests",
        "data",
        "results",
        "docs",
        "code/data",
        "code/analysis",
        "code/viz",
        "tests/unit",
        "tests/contract",
        "tests/integration",
    ]

    # Create directories
    for d in directories:
        full_path = os.path.join(base_dir, d)
        ensure_dir(full_path)

    # Define __init__.py files to create
    init_files = [
        "code/__init__.py",
        "code/data/__init__.py",
        "code/analysis/__init__.py",
        "code/viz/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/contract/__init__.py",
        "tests/integration/__init__.py",
    ]

    # Create init files
    for init_file in init_files:
        full_path = os.path.join(base_dir, init_file)
        create_init_file(full_path)

    print("\nProject structure initialization complete.")

if __name__ == "__main__":
    main()