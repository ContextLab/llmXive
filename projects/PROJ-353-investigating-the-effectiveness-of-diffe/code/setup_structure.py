"""
Project Structure Initialization Script.

This script creates the required directory structure for the llmXive project
and verifies their existence before exiting.
"""
import os
import sys
from pathlib import Path

def main():
    """Create and verify the project directory structure."""
    # Define the required directories relative to the project root
    # We assume the script is run from the project root or code/ directory.
    # We will resolve paths relative to the current working directory.
    root = Path.cwd()
    
    required_dirs = [
        "code",
        "tests",
        "data",
        "data/raw",
        "data/processed",
        "data/analysis",
        "artifacts",
        "contracts"
    ]

    print(f"Initializing project structure in: {root}")
    
    created_count = 0
    existing_count = 0

    for dir_path in required_dirs:
        full_path = root / dir_path
        
        if not full_path.exists():
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {full_path}")
                created_count += 1
            except OSError as e:
                print(f"ERROR: Failed to create directory {full_path}: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            if full_path.is_dir():
                print(f"Directory already exists: {full_path}")
                existing_count += 1
            else:
                print(f"ERROR: Path exists but is not a directory: {full_path}", file=sys.stderr)
                sys.exit(1)

    # Verification: Ensure all directories exist
    print("\n--- Verification ---")
    all_exist = True
    for dir_path in required_dirs:
        full_path = root / dir_path
        if not (full_path.exists() and full_path.is_dir()):
            print(f"FAIL: Directory missing or invalid: {full_path}")
            all_exist = False
        else:
            print(f"OK: {full_path}")

    if not all_exist:
        print("\nVERIFICATION FAILED: Not all required directories exist.", file=sys.stderr)
        sys.exit(1)

    print(f"\nSuccess: Created {created_count} new directories. Verified {existing_count + created_count} total.")
    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()
