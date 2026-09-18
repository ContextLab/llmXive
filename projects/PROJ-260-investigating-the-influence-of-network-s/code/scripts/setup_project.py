import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the project directory structure as defined in task T001a.
    All paths are relative to the project root (current working directory).
    """
    # Define all required directories relative to the project root
    base_dirs = [
        "src",
        "tests",
        "data",
        "outputs",
        "data/metadata",
        "data/derived",
        "data/derived/topology",
        "data/derived/vdos",
        "data/derived/reference",
        "data/derived/correlation",
        "outputs/figures",
        "outputs/reports",
    ]

    created_count = 0
    for dir_path in base_dirs:
        full_path = Path(dir_path)
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
        else:
            # Ensure it is actually a directory
            if not full_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")

    print(f"Directory structure created/verified. New directories: {created_count}")
    return True

def main():
    """Entry point for the script."""
    try:
        create_directories()
        print("Task T001a completed successfully.")
    except Exception as e:
        print(f"Error creating directory structure: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()