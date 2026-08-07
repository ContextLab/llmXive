import os
from pathlib import Path
import sys

def setup_directories():
    """
    Creates the required project directory structure as per the implementation plan.
    This satisfies Task T001: Create project structure per implementation plan.
    
    Required directories:
    - src/ (source code)
    - tests/ (unit and integration tests)
    - data/ (raw, derived, gold_standard, artifacts)
    - specs/001-gene-regulation/ (design documents and contracts)
    """
    base_dir = Path(__file__).parent.parent
    
    # Define the directory structure relative to the project root
    directories = [
        "src",
        "src/lib",
        "src/services",
        "src/cli",
        "src/models",
        "src/analysis",
        "tests",
        "tests/unit",
        "tests/integration",
        "data",
        "data/raw",
        "data/derived",
        "data/gold_standard",
        "artifacts",
        "specs",
        "specs/001-gene-regulation",
        "specs/001-gene-regulation/contracts",
    ]
    
    created_count = 0
    existing_count = 0
    
    print(f"Setting up project structure in: {base_dir}")
    
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  Created: {dir_path}")
            created_count += 1
        else:
            # Check if it's a directory
            if full_path.is_dir():
                existing_count += 1
            else:
                # It's a file with the same name, which is an error
                print(f"  ERROR: Path exists but is not a directory: {dir_path}")
                sys.exit(1)
    
    print(f"\nProject structure setup complete.")
    print(f"  Created: {created_count} directories")
    print(f"  Existing: {existing_count} directories")
    
    return True

if __name__ == "__main__":
    setup_directories()
