import os
import sys
from pathlib import Path

def main():
    """
    Creates the project directory structure as per the implementation plan.
    This script ensures all required directories for data, source code, and tests exist.
    """
    project_root = Path(__file__).resolve().parent.parent
    
    # Define directory structure based on tasks.md and plan.md
    directories = [
        # Source code structure
        project_root / "src",
        project_root / "src" / "utils",
        project_root / "src" / "data",
        project_root / "src" / "analysis",
        project_root / "src" / "cli",
        
        # Data structure
        project_root / "data",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "traits",
        project_root / "data" / "manifests",
        project_root / "data" / "synthetic",
        
        # Tests structure
        project_root / "tests",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
        project_root / "tests" / "contract",
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory.relative_to(project_root)}")
            created_count += 1
        else:
            print(f"Directory exists: {directory.relative_to(project_root)}")
    
    # Create .gitkeep files to ensure directories are tracked in git
    gitkeep_content = "# This file ensures the directory is tracked in version control.\n"
    for directory in directories:
        gitkeep_path = directory / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.write_text(gitkeep_content)
            print(f"Created .gitkeep in: {directory.relative_to(project_root)}")
    
    print(f"\nProject structure setup complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())