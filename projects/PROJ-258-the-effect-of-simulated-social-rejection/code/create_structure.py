"""
Project Structure Initialization Script.

Creates the required directory tree for the llmXive automated science pipeline:
- code/
- data/raw/
- data/interim/
- data/processed/
- tests/
- reports/
- docs/
- specs/
- data/figures/
- state/
"""
import os
import sys
from pathlib import Path

def main():
    """Create the project directory structure."""
    base_dir = Path(__file__).resolve().parent.parent
    
    required_dirs = [
        "code",
        "data/raw",
        "data/interim",
        "data/processed",
        "data/figures",
        "tests",
        "reports",
        "docs",
        "specs",
        "state",
    ]
    
    created_count = 0
    existing_count = 0
    
    print(f"Initializing project structure at: {base_dir}")
    
    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path.relative_to(base_dir)}")
            created_count += 1
        else:
            existing_count += 1
    
    print(f"Structure initialization complete.")
    print(f"  - New directories created: {created_count}")
    print(f"  - Existing directories: {existing_count}")
    
    # Verify structure
    missing = []
    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        if not full_path.exists():
            missing.append(dir_path)
    
    if missing:
        print(f"ERROR: Missing directories: {missing}")
        sys.exit(1)
    else:
        print("Verification passed: All required directories exist.")
        sys.exit(0)

if __name__ == "__main__":
    main()
