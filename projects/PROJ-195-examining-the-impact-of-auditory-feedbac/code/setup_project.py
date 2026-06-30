"""
Setup script to create the project directory structure for PROJ-195.
This script creates all necessary directories as defined in T001a.
"""
import os
import sys

def main():
    # Project root relative to this script's location (assuming script is in code/)
    # We go up one level to get the project root
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    # Define the project name based on the task description
    project_name = "PROJ-195-examining-the-impact-of-auditory-feedbac"
    
    # Full path to the project directory
    project_path = os.path.join(project_root, project_name)
    
    # Define the subdirectories to create
    # Based on T001a: code, data/raw, data/derivatives, data/processed, roi_masks,
    # tests/unit, tests/integration, tests/contract
    subdirectories = [
        "code",
        "data/raw",
        "data/derivatives",
        "data/processed",
        "roi_masks",
        "tests/unit",
        "tests/integration",
        "tests/contract"
    ]
    
    print(f"Creating project structure for: {project_name}")
    print(f"Project path: {project_path}")
    
    created_count = 0
    existing_count = 0
    
    for subdir in subdirectories:
        full_path = os.path.join(project_path, subdir)
        try:
            if not os.path.exists(full_path):
                os.makedirs(full_path, exist_ok=True)
                print(f"  Created: {full_path}")
                created_count += 1
            else:
                print(f"  Exists:  {full_path}")
                existing_count += 1
        except OSError as e:
            print(f"  ERROR: Failed to create {full_path}: {e}")
            sys.exit(1)
    
    print(f"\nProject structure setup complete.")
    print(f"  Directories created: {created_count}")
    print(f"  Directories existing: {existing_count}")
    print(f"  Total: {len(subdirectories)}")

if __name__ == "__main__":
    main()
