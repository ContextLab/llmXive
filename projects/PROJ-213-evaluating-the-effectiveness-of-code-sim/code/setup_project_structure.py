"""
T005: Create project structure per implementation plan.

This script initializes the directory structure required for the
PROJ-213-evaluating-the-effectiveness-of-code-simplification project.

It creates:
- data/raw/
- data/processed/
- data/logs/
- code/
- tests/
- state/

It also creates .gitkeep files to ensure directories are tracked by git.
"""
import os
from pathlib import Path

def main():
    # Define the project root (current working directory context)
    # In the context of this task, we assume execution from the project root
    project_root = Path.cwd()

    # Define the required directories relative to the project root
    directories = [
        "data/raw",
        "data/processed",
        "data/logs",
        "code",
        "tests",
        "state",
        # Subdirectories often needed for tests
        "tests/unit",
        "tests/contract",
        "tests/integration",
        # Specs directory mentioned in task description context
        "specs/001-eval-code-simplification",
    ]

    created_dirs = []
    errors = []

    for dir_path_str in directories:
        dir_path = project_root / dir_path_str
        try:
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                created_dirs.append(dir_path_str)
            
            # Create .gitkeep to ensure directory is tracked
            gitkeep_path = dir_path / ".gitkeep"
            if not gitkeep_path.exists():
                gitkeep_path.write_text("# Keep this directory in git\n")
                
        except PermissionError:
            errors.append(f"Permission denied creating: {dir_path_str}")
        except Exception as e:
            errors.append(f"Error creating {dir_path_str}: {str(e)}")

    # Output summary
    print(f"Project structure initialization complete.")
    print(f"Directories created: {len(created_dirs)}")
    for d in created_dirs:
        print(f"  - {d}")
    
    if errors:
        print(f"Errors encountered: {len(errors)}")
        for err in errors:
            print(f"  ! {err}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())