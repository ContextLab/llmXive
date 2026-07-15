import os
import sys
from pathlib import Path

def main():
    """
    Main entry point to ensure the project directory structure exists.
    This script is the executable artifact for Task T001.
    """
    # Determine the project root (parent of the code/ directory)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent

    print(f"Project Root: {project_root}")
    
    # Define the required directories relative to project root
    # Based on tasks.md: code/, tests/, data/, results/
    # Plus subdirectories for processed data and benchmarks
    required_paths = [
        "code",
        "tests",
        "data",
        "data/processed",
        "results",
        "results/benchmarks",
        "figures",
        "specs"
    ]

    created_count = 0
    existing_count = 0

    for rel_path in required_paths:
        full_path = project_root / rel_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created: {full_path}")
        else:
            if not full_path.is_dir():
                print(f"Error: Path exists but is not a directory: {full_path}")
                sys.exit(1)
            existing_count += 1

    print(f"\nSetup complete. Created: {created_count}, Existing: {existing_count}")
    
    # Verify structure
    missing = []
    for rel_path in required_paths:
        if not (project_root / rel_path).is_dir():
            missing.append(rel_path)
    
    if missing:
        print(f"Error: Missing directories after setup: {missing}")
        sys.exit(1)
    
    print("All required directories verified.")

if __name__ == "__main__":
    main()
