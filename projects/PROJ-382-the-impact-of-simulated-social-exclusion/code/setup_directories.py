"""
Script to initialize the project directory structure for PROJ-382.
Creates the necessary folders for code, data (raw/processed), tests, and state.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root relative to where this script is run
    # Assuming the script is run from the project root or code directory
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent if current_dir.name == "code" else current_dir

    # Define the required directory structure
    # Based on task T001a: projects/PROJ-382-the-impact-of-simulated-social-exclusion/code/...
    # We assume this script is running inside the 'code' folder or the project root.
    # We will create the subdirectories relative to the project root.
    
    base_path = project_root / "projects" / "PROJ-382-the-impact-of-simulated-social-exclusion"
    
    # If the script is already inside the project root, adjust base_path
    # Check if we are already at the specific project folder
    if "PROJ-382-the-impact-of-simulated-social-exclusion" in str(project_root):
        base_path = project_root
    
    # Ensure we are not creating directories in the wrong place if run from repo root
    # The task specifies the path: projects/PROJ-382-the-impact-of-simulated-social-exclusion/...
    # We will create this structure relative to the current working directory if not already present.
    
    # Let's assume the project root is the directory containing this script's parent 'code' folder
    # or the script is run from the repo root.
    
    # To be safe and adhere strictly to the path in the task:
    # We will create the full path structure starting from the current working directory
    # if the specific project folder doesn't exist.
    
    target_root = Path.cwd() / "projects" / "PROJ-382-the-impact-of-simulated-social-exclusion"
    
    # If the script is located in a 'code' folder that is already inside the target, adjust
    script_dir = Path(__file__).resolve().parent
    if "code" in script_dir.parts and "PROJ-382-the-impact-of-simulated-social-exclusion" in script_dir.parts:
        target_root = script_dir.parent
    
    directories = [
        target_root / "code",
        target_root / "data" / "raw",
        target_root / "data" / "processed",
        target_root / "tests",
        target_root / "state"
    ]

    created_count = 0
    skipped_count = 0

    print(f"Initializing directory structure at: {target_root}")

    for dir_path in directories:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            if dir_path.exists():
                print(f"Created/Verified: {dir_path}")
                created_count += 1
            else:
                print(f"Warning: Failed to create {dir_path}")
        except PermissionError:
            print(f"Error: Permission denied creating {dir_path}")
        except Exception as e:
            print(f"Error creating {dir_path}: {e}")

    print(f"Directory setup complete. Created/Verified: {created_count}, Skipped/Failed: {skipped_count}")

    # Verify the structure matches the task requirement
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "tests",
        "state"
    ]

    all_good = True
    for rel_dir in required_dirs:
        if not (target_root / rel_dir).exists():
            print(f"Verification Failed: {target_root / rel_dir} does not exist.")
            all_good = False

    if all_good:
        print("Verification Passed: All required directories exist.")
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())
