#!/usr/bin/env python3
"""
Script to initialize the project root structure for PROJ-898-llmxive-follow-up-extending-geometric-ac.

This script creates the necessary directory structure and placeholder files
as specified in the implementation plan.
"""

import os
import sys

def main():
    """Initialize the project structure."""
    # Get the current working directory as project root
    project_root = os.getcwd()
    
    # Define all directories to create
    directories = [
        "code",
        "data/raw",
        "data/generated", 
        "data/results",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "scripts",
        "figures",
        "specs"
    ]
    
    print(f"Initializing project structure in: {project_root}")
    print("-" * 60)
    
    # Create directories
    for dir_path in directories:
        full_path = os.path.join(project_root, dir_path)
        os.makedirs(full_path, exist_ok=True)
        print(f"✓ Created: {dir_path}")
    
    # Create .gitkeep files in data subdirectories
    data_subdirs = ["data/raw", "data/generated", "data/results"]
    print("-" * 60)
    
    for subdir in data_subdirs:
        dir_path = os.path.join(project_root, subdir)
        gitkeep_path = os.path.join(dir_path, ".gitkeep")
        
        if not os.path.exists(gitkeep_path):
            with open(gitkeep_path, "w") as f:
                f.write("# Git keeps this directory in version control\n")
            print(f"✓ Created: {subdir}/.gitkeep")
        else:
            print(f"  Exists: {subdir}/.gitkeep")
    
    # Create placeholder files in tests directories
    tests_dirs = ["tests/unit", "tests/integration", "tests/contract"]
    print("-" * 60)
    
    for tests_dir in tests_dirs:
        init_path = os.path.join(project_root, tests_dir, "__init__.py")
        if not os.path.exists(init_path):
            with open(init_path, "w") as f:
                f.write("# Test package\n")
            print(f"✓ Created: {tests_dir}/__init__.py")
        else:
            print(f"  Exists: {tests_dir}/__init__.py")
    
    # Create placeholder __init__.py in code directory
    code_init = os.path.join(project_root, "code", "__init__.py")
    if not os.path.exists(code_init):
        with open(code_init, "w") as f:
            f.write("# Code package\n")
        print(f"✓ Created: code/__init__.py")
    else:
        print(f"  Exists: code/__init__.py")
    
    print("-" * 60)
    print("Project structure initialization complete.")
    print("\nDirectory structure created:")
    print("  code/")
    print("  data/")
    print("    ├── raw/")
    print("    ├── generated/")
    print("    └── results/")
    print("  tests/")
    print("    ├── unit/")
    print("    ├── integration/")
    print("    └── contract/")
    print("  scripts/")
    print("  figures/")
    print("  specs/")

if __name__ == "__main__":
    main()
