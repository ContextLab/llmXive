"""
Project structure initialization script.
Creates the required directory tree for the llmXive research pipeline.
"""
import os
import sys
from pathlib import Path

# Define the required directory structure relative to project root
REQUIRED_DIRS = [
    "code/data",
    "code/training",
    "code/evaluation",
    "code/utils",
    "code/tests",
    "data/raw/gsm8k",
    "data/raw/logiqa",
    "data/processed",
    "data/artifacts/results",
    "contracts",
    "docs",
]

def main():
    """Create all required directories if they do not exist."""
    base_path = Path(__file__).resolve().parent.parent.parent
    created_count = 0
    
    for dir_path in REQUIRED_DIRS:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory exists: {full_path}")
    
    print(f"\nProject structure initialization complete.")
    print(f"Directories created: {created_count}")
    print(f"Directories verified: {len(REQUIRED_DIRS)}")
    
    # Verify all exist at the end
    all_exist = all((base_path / d).exists() for d in REQUIRED_DIRS)
    if not all_exist:
        print("ERROR: Some directories were not created successfully.")
        sys.exit(1)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())