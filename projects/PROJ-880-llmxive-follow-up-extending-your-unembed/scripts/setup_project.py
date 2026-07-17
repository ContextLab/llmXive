"""
Script to initialize the project directory structure.
This script creates the necessary directories as defined in plan.md.
"""
import os
import sys

def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Define directories based on plan.md and tasks.md
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "tests",
        "contracts",
        "specs",
        "figures",
    ]
    
    created = []
    for d in directories:
        path = os.path.join(root, d)
        if not os.path.exists(path):
            os.makedirs(path)
            created.append(d)
        else:
            print(f"Directory exists: {d}")
    
    if created:
        print(f"Created directories: {', '.join(created)}")
    else:
        print("All directories already exist.")
    
    # Create __init__.py files in Python packages
    init_files = [
        os.path.join(root, "code", "__init__.py"),
        os.path.join(root, "data", "__init__.py"),
        os.path.join(root, "tests", "__init__.py"),
        os.path.join(root, "contracts", "__init__.py"),
    ]
    
    for f in init_files:
        if not os.path.exists(f):
            with open(f, 'w') as fh:
                fh.write("# Auto-generated init file\n")
            print(f"Created: {f}")
        else:
            print(f"Init file exists: {f}")

if __name__ == "__main__":
    main()
