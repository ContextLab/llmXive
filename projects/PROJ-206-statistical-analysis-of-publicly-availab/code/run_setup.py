"""
Runner script to execute T004 setup and verify directory creation.
This script ensures the data directory structure is created and prints a verification report.
"""
import os
import sys
from pathlib import Path

def main():
    # Determine project root
    current_path = Path(__file__).resolve()
    project_root = current_path.parent
    
    # If running from code/, go up one level
    if current_path.name == 'run_setup.py' and current_path.parent.name == 'code':
        project_root = current_path.parent
    elif current_path.parent.name == 'code' and current_path.parent.parent.name == 'code':
        project_root = current_path.parent.parent.parent
    
    # Fallback to cwd
    if not (project_root / 'data').exists() and not (project_root / 'state').exists():
        project_root = Path.cwd()

    print(f"Running T004 Setup for project root: {project_root}")

    # Define directories
    dirs_to_create = [
        project_root / 'data' / 'raw',
        project_root / 'data' / 'processed',
        project_root / 'state' / 'projects'
    ]

    success = True
    for d in dirs_to_create:
        try:
            d.mkdir(parents=True, exist_ok=True)
            print(f"  [OK] Created/Verified: {d}")
        except Exception as e:
            print(f"  [FAIL] Failed to create {d}: {e}")
            success = False

    if success:
        print("\nT004 Setup Complete. All directories verified.")
        # List contents to prove existence
        print("\nDirectory Listing:")
        for d in dirs_to_create:
            print(f"  {d}: {list(d.iterdir())}")
    else:
        print("\nT004 Setup Failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()