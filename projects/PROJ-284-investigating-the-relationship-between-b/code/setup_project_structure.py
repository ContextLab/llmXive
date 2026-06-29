"""
Script to initialize the project directory structure for PROJ-284.
Creates all necessary folders for code, data, logs, and documentation.
"""
import os
import sys

def main():
    # Define the relative paths to create based on the task specification
    # All paths are relative to the project root
    directories = [
        # Code organization
        "code/data",
        "code/analysis",
        "code/viz",
        "code/report",
        "code/tests",
        
        # Data organization
        "data/raw",
        "data/processed",
        "data/analysis",
        
        # Infrastructure
        "logs",
        "docs"
    ]

    created_count = 0
    existing_count = 0

    print("Initializing project structure for PROJ-284...")
    
    for dir_path in directories:
        try:
            if os.path.exists(dir_path):
                existing_count += 1
                print(f"  [SKIP] {dir_path} (already exists)")
            else:
                os.makedirs(dir_path, exist_ok=True)
                created_count += 1
                print(f"  [CREATED] {dir_path}")
        except OSError as e:
            print(f"  [ERROR] Failed to create {dir_path}: {e}")
            sys.exit(1)

    print(f"\nProject structure initialization complete.")
    print(f"  Directories created: {created_count}")
    print(f"  Directories skipped: {existing_count}")
    print(f"  Total directories: {len(directories)}")

if __name__ == "__main__":
    main()
