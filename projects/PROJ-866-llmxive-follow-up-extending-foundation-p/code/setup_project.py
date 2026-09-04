import os
import sys
from pathlib import Path

def create_structure():
    """
    Creates the core project directory structure as per the implementation plan.
    Directories created:
    - code/ (source code)
    - data/raw/ (raw generated data)
    - data/processed/ (processed execution logs)
    - data/results/ (analysis results, regression data)
    - tests/ (unit, integration, contract tests)
    - state/ (project state registry)
    - state/projects/ (project-specific state files)
    """
    root = Path.cwd()
    
    # Define the directory structure relative to the root
    directories = [
        "code",
        "code/analysis",
        "code/engines",
        "code/generators",
        "code/utils",
        "data",
        "data/raw",
        "data/processed",
        "data/results",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "state",
        "state/projects",
    ]
    
    created = []
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(str(full_path))
        else:
            # Ensure it is actually a directory if it exists
            if not full_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")
    
    return created

def main():
    """Entry point for running the script directly."""
    print("Creating project structure...")
    try:
        created_dirs = create_structure()
        print(f"Successfully created {len(created_dirs)} directories:")
        for d in created_dirs:
            print(f"  - {d}")
    except Exception as e:
        print(f"Error creating project structure: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
