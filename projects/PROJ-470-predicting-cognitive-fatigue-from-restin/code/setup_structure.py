"""
Project structure setup script for PROJ-470-predicting-cognitive-fatigue-from-restin.
Creates the required directory hierarchy for the automated science pipeline.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the project directory structure."""
    # Define the project root relative to the current working directory
    project_root = Path.cwd()
    
    # Define all required directories
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/analysis",
        "code",
        "tests/unit",
        "tests/integration",
        "docs",
        "specs"  # Added for spec files as referenced in task descriptions
    ]
    
    created_count = 0
    existing_count = 0
    
    print(f"Setting up project structure in: {project_root}")
    print("-" * 60)
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        
        if full_path.exists():
            if full_path.is_dir():
                print(f"[EXISTS] {dir_path}")
                existing_count += 1
            else:
                print(f"[ERROR] {dir_path} exists but is not a directory!")
                sys.exit(1)
        else:
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"[CREATED] {dir_path}")
                created_count += 1
            except Exception as e:
                print(f"[ERROR] Failed to create {dir_path}: {e}")
                sys.exit(1)
    
    # Create .gitkeep files to ensure directories are tracked by git
    gitkeep_files = []
    for dir_path in required_dirs:
        full_path = project_root / dir_path / ".gitkeep"
        if not full_path.exists():
            full_path.touch()
            gitkeep_files.append(str(full_path))
    
    print("-" * 60)
    print(f"Summary: {created_count} directories created, {existing_count} already existed.")
    print(f"Created {len(gitkeep_files)} .gitkeep files to ensure git tracking.")
    print("Project structure setup complete.")
    
    # Print the resulting tree structure for verification
    print("\nResulting directory structure:")
    print("├── data/")
    print("│   ├── analysis/")
    print("│   ├── processed/")
    print("│   └── raw/")
    print("├── code/")
    print("├── docs/")
    print("├── specs/")
    print("└── tests/")
    print("    ├── integration/")
    print("    └── unit/")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
