"""
T001: Create project structure per implementation plan.
Creates directories: src/, tests/, data/, specs/, data/raw/, data/results/, figures/
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root relative to where the script is run
    # The script expects to be run from the project root or code/
    base_path = Path(__file__).parent.parent
    
    # Define required directories based on tasks.md and plan.md
    # Paths are relative to the project root
    directories = [
        "src",
        "src/lib",
        "src/data",
        "src/models",
        "src/analysis",
        "src/cli",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "data",
        "data/raw",
        "data/results",
        "figures",
        "specs",
        "docs",
    ]

    created_count = 0
    existing_count = 0

    for dir_name in directories:
        full_path = base_path / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            existing_count += 1
            # Optional: verify it is a directory
            if not full_path.is_dir():
                print(f"Warning: {full_path} exists but is not a directory.")

    # Create __init__.py files to make src and tests proper packages
    # This helps with imports and IDE recognition
    init_files = [
        "src/__init__.py",
        "src/lib/__init__.py",
        "src/data/__init__.py",
        "src/models/__init__.py",
        "src/analysis/__init__.py",
        "src/cli/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py",
        "tests/contract/__init__.py",
    ]

    for init_file in init_files:
        full_path = base_path / init_file
        if not full_path.exists():
            full_path.touch()
            # Add a simple docstring or comment
            with open(full_path, 'w') as f:
                f.write(f"# {init_file}\n")
            print(f"Created init file: {full_path}")
            created_count += 1

    print(f"\nProject structure setup complete.")
    print(f"Created {created_count} new items, {existing_count} already existed.")
    
    # Verify critical directories exist
    critical_dirs = ["src", "tests", "data", "data/raw", "data/results"]
    missing = []
    for d in critical_dirs:
        if not (base_path / d).is_dir():
            missing.append(d)
    
    if missing:
        print(f"ERROR: Missing critical directories: {missing}")
        sys.exit(1)
    
    print("All critical directories verified.")

if __name__ == "__main__":
    main()
