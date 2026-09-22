"""
T001: Create project structure per plan.md.
This script creates the required directory hierarchy for the llmXive project.
It ensures all necessary directories exist before any pipeline stages run.
"""
import os
from pathlib import Path

# Define the directory structure based on plan.md and tasks.md conventions
# Paths are relative to the project root (where this script is run from)
REQUIRED_DIRS = [
    "code",
    "code/utils",
    "tests",
    "tests/unit",
    "tests/integration",
    "data",
    "data/raw",
    "data/filtered",
    "data/traces",
    "data/results",
    "data/validation",
    "data/pilot",
    "specs",
    "specs/001-blind-spots-order-analysis",
    "specs/001-blind-spots-order-analysis/contracts",
    "state",
    "figures",
]

def create_directories():
    """Create all required directories if they do not exist."""
    root = Path(".")
    created_count = 0
    skipped_count = 0

    print("Creating project directory structure...")
    
    for dir_path_str in REQUIRED_DIRS:
        dir_path = root / dir_path_str
        
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {dir_path}")
            created_count += 1
        else:
            # Check if it's actually a directory
            if dir_path.is_dir():
                print(f"Exists: {dir_path}")
                skipped_count += 1
            else:
                raise RuntimeError(f"Path exists but is not a directory: {dir_path}")

    print(f"\nDirectory creation complete.")
    print(f"  Created: {created_count}")
    print(f"  Already existed: {skipped_count}")
    print(f"  Total: {created_count + skipped_count}")
    
    # Verify critical paths
    critical_paths = ["code", "tests", "data/filtered", "data/traces"]
    for path_str in critical_paths:
        path = root / path_str
        if not path.exists() or not path.is_dir():
            raise RuntimeError(f"Critical path missing after creation: {path}")
    
    print("\nVerification passed: All critical paths exist.")

if __name__ == "__main__":
    create_directories()
