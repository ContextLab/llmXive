"""
Script to create the project directory structure for llmXive Follow-up.
This implements T001 by creating all required directories relative to the project root.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root (assuming script is run from root or code/)
    # We determine the root by looking for the 'code' directory or assuming current dir is root
    current_dir = Path.cwd()
    
    # Check if we are inside 'code' or at root. 
    # If 'code' exists in current dir, we are at root. 
    # If 'setup_project_structure.py' is in 'code', we might need to go up one level if 'data' is expected at root.
    # Based on tasks.md: "All artifact paths are relative to the project root and MUST live under code/, data/..."
    # The script itself is in 'code/', so the root is likely the parent of 'code/'.
    
    project_root = current_dir
    if (current_dir / "code").is_dir() and (current_dir / "data").is_dir():
        # Already at root
        project_root = current_dir
    elif (current_dir / "code").is_dir():
        # If we are in code/, go up
        project_root = current_dir.parent

    # Define directories relative to project root
    # Note: specs path includes a deep nested structure as per task description
    dirs_to_create = [
        "data/raw",
        "data/processed",
        "code",
        "code/utils",
        "code/tests",
        "results",
        "artifacts",
        "specs/001-reward-fidelity-error-recovery/contracts"
    ]

    created_count = 0
    existing_count = 0

    print(f"Project Root identified at: {project_root}")
    print("Creating directory structure...")

    for dir_path in dirs_to_create:
        full_path = project_root / dir_path
        
        if full_path.exists():
            print(f"  [SKIP] {dir_path} (already exists)")
            existing_count += 1
        else:
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"  [OK] Created: {dir_path}")
                created_count += 1
            except OSError as e:
                print(f"  [ERROR] Failed to create {dir_path}: {e}")
                sys.exit(1)

    print(f"\nSummary: {created_count} directories created, {existing_count} already existed.")
    
    # Verification step: List all created directories
    print("\nVerification (ls):")
    for dir_path in dirs_to_create:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"  {full_path}")
        else:
            print(f"  MISSING: {full_path}")
            sys.exit(1)

    print("\nAll directories verified successfully.")

if __name__ == "__main__":
    main()