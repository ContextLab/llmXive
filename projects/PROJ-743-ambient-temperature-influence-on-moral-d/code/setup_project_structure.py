"""
T007: Create project structure per implementation plan.
Creates the required directory tree for the project.
"""
import os
import sys
from pathlib import Path

def ensure_directories():
    """Create the required project directories."""
    # Define the base directory relative to the script location or current working directory
    # The task specifies paths relative to project root.
    base_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "results/figures",
        "results/logs",
        "results/stats",
        "tests"
    ]

    created_count = 0
    for dir_path in base_dirs:
        full_path = Path(dir_path)
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    return created_count

def main():
    print("Initializing project structure for PROJ-743...")
    count = ensure_directories()
    print(f"Project structure initialization complete. {count} new directories created.")
    # Verify existence of critical paths required for downstream tasks
    critical_paths = [
        "data/raw",
        "data/processed",
        "results/logs",
        "results/figures",
        "results/stats"
    ]
    missing = [p for p in critical_paths if not Path(p).exists()]
    if missing:
        print(f"ERROR: Missing critical directories: {missing}")
        sys.exit(1)
    print("All critical directories verified.")

if __name__ == "__main__":
    main()
