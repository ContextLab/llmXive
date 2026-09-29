"""
Script to create the project directory structure for PROJ-080.
This satisfies Task T001: Create project structure per implementation plan.
"""
import os
import sys

def main():
    # Define the base project root
    project_root = "projects/PROJ-080-phase-transitions-in-amorphous-solids-un"
    
    # Define the required directories relative to the project root
    required_dirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests/unit",
        "tests/integration",
        "specs/contracts"
    ]
    
    created_count = 0
    skipped_count = 0

    print(f"Creating project structure for: {project_root}")
    
    # Ensure the base root exists first
    if not os.path.exists(project_root):
        os.makedirs(project_root)
        print(f"  Created base directory: {project_root}")
        created_count += 1
    else:
        print(f"  Base directory exists: {project_root}")
    
    # Create subdirectories
    for dir_path in required_dirs:
        full_path = os.path.join(project_root, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            print(f"  Created: {full_path}")
            created_count += 1
        else:
            print(f"  Exists: {full_path}")
            skipped_count += 1

    print(f"\nSummary: {created_count} directories created, {skipped_count} already existed.")
    print("Project structure setup complete.")

if __name__ == "__main__":
    main()