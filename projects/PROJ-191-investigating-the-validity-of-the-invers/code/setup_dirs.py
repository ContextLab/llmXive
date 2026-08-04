"""
Script to create the full project directory tree for PROJ-191.
Executes a single atomic operation to ensure all required sub-directories exist.
"""
import os
import sys
from pathlib import Path

# Define the project root relative to the code directory
# The project root is the parent of 'code'
CURRENT_FILE = Path(__file__)
PROJECT_ROOT = CURRENT_FILE.parent.parent
PROJECT_NAME = "PROJ-191-investigating-the-validity-of-the-invers"
PROJECT_DIR = PROJECT_ROOT / "projects" / PROJECT_NAME

# Define all required sub-directories relative to the project root
REQUIRED_DIRS = [
    "code",
    "tests",
    "data",
    "docs",
    "code/data",
    "code/models",
    "code/inference",
    "code/robustness",
    "code/utils",
    "data/raw",
    "data/processed",
    "data/results",
    "tests/unit",
    "tests/contract",
    "tests/integration",
]

def main():
    """
    Creates the full directory tree in a single atomic operation.
    Uses exist_ok=True to ensure idempotency (safe to run multiple times).
    """
    print(f"Target Project Directory: {PROJECT_DIR}")
    
    # Ensure the root project directory exists first
    PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    
    created_count = 0
    for dir_path in REQUIRED_DIRS:
        full_path = PROJECT_DIR / dir_path
        # mkdir with parents=True handles nested creation in one call
        full_path.mkdir(parents=True, exist_ok=True)
        created_count += 1
    
    print(f"Successfully created/verified {created_count} sub-directories under {PROJECT_NAME}.")
    
    # Verification: List the created structure to stdout for immediate feedback
    print("\nCreated Directory Structure:")
    for dir_path in REQUIRED_DIRS:
        full_path = PROJECT_DIR / dir_path
        # Verify existence explicitly
        if not full_path.exists():
            raise RuntimeError(f"Failed to create directory: {full_path}")
        print(f"  [OK] {full_path.relative_to(PROJECT_DIR)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
