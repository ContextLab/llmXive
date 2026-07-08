"""
Script to initialize the project directory structure for PROJ-550.
Creates the necessary folders for code, data, tests, and documentation.
"""
import os
import sys
from pathlib import Path

def main():
    # Project root relative to the working directory
    project_root = Path("projects/PROJ-550-exploring-the-convergence-of-iterated-fu")
    
    # Define the subdirectories to create
    subdirs = [
        "code",
        "data/raw",
        "data/derived",
        "tests/unit",
        "tests/contract",
        "docs"
    ]
    
    created_count = 0
    skipped_count = 0
    
    print(f"Initializing project structure at: {project_root.absolute()}")
    
    for subdir in subdirs:
        target_path = project_root / subdir
        try:
            target_path.mkdir(parents=True, exist_ok=True)
            if target_path.exists():
                print(f"  [OK] Created: {subdir}")
                created_count += 1
            else:
                print(f"  [WARN] Failed to create: {subdir}")
        except Exception as e:
            print(f"  [ERROR] Could not create {subdir}: {e}")
    
    # Create __init__.py files to make directories Python packages where appropriate
    package_dirs = [
        "code",
        "tests/unit",
        "tests/contract"
    ]
    
    for pkg_dir in package_dirs:
        init_file = project_root / pkg_dir / "__init__.py"
        try:
            if not init_file.exists():
                init_file.write_text("")
                print(f"  [OK] Created package init: {pkg_dir}/__init__.py")
                created_count += 1
        except Exception as e:
            print(f"  [WARN] Could not create init file for {pkg_dir}: {e}")

    print(f"\nSetup complete. Created {created_count} directories/files, skipped {skipped_count}.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
