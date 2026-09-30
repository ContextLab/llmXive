"""
Project Structure Initialization Script for llmXive PROJ-212.

This script creates the required directory hierarchy as specified in the
implementation plan. It ensures all necessary folders for code, tests,
data (raw/processed), results, and state management exist.
"""
import os
import sys
from pathlib import Path

def main():
    # Determine the project root based on the execution context.
    # The script is expected to be run from the project root or code/ directory.
    # We will create the structure relative to the current working directory
    # to ensure it lands in the correct place for the runner.
    
    # Define the relative paths to create
    # Based on tasks.md: `mkdir -p src tests data results data/raw data/processed state`
    # The task description also mentions `projects/PROJ-212-exploring-the-impact-of-network-structur/code/`
    # We will create these directories relative to the current working directory.
    
    required_dirs = [
        "src",
        "tests",
        "data",
        "results",
        "data/raw",
        "data/processed",
        "state"
    ]

    base_path = Path.cwd()
    
    print(f"Initializing project structure in: {base_path}")
    
    created_count = 0
    existing_count = 0

    for dir_name in required_dirs:
        target_path = base_path / dir_name
        
        if target_path.exists():
            print(f"[SKIP] Directory already exists: {target_path}")
            existing_count += 1
        else:
            target_path.mkdir(parents=True, exist_ok=True)
            print(f"[CREATE] Directory created: {target_path}")
            created_count += 1

    # Verify the structure
    print("\n--- Project Structure Verification ---")
    missing = []
    for dir_name in required_dirs:
        target_path = base_path / dir_name
        if not target_path.exists():
            missing.append(dir_name)
            print(f"[FAIL] Missing: {target_path}")
        else:
            print(f"[OK] Present: {target_path}")
    
    if missing:
        print(f"\nError: Failed to create {len(missing)} directories.")
        sys.exit(1)
    else:
        print(f"\nSuccess: All {len(required_dirs)} directories created or verified.")
        print(f"Created: {created_count}, Existing: {existing_count}")
        return 0

if __name__ == "__main__":
    sys.exit(main())