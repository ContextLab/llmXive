"""
Script to initialize the project directory structure for PROJ-455.
Creates all necessary directories for code, tests, contracts, and data.
"""
import os
import sys

# Define the relative paths to create based on the task description
# All paths are relative to the project root
directories = [
    "code/data",
    "code/models",
    "code/analysis",
    "tests/unit",
    "tests/integration",
    "tests/contract",
    "tests/benchmark",
    "contracts",
    "data/raw",
    "data/processed",
    "data/results",
]

def main():
    # Determine the project root. 
    # If run as `python code/setup_project.py`, the root is the parent of 'code'.
    # If run as `python code/setup_project.py` from root, we handle both.
    # We assume the script is executed from the repository root or the project root.
    # To be safe, we resolve the directory containing the script and go up one level 
    # if the script is inside 'code', or stay if it's at root (though this script is in code/).
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Since this script is in code/, the project root is the parent of code/
    project_root = os.path.dirname(script_dir)

    created_count = 0
    skipped_count = 0

    print(f"Project root detected at: {project_root}")

    for dir_path in directories:
        full_path = os.path.join(project_root, dir_path)
        
        if os.path.exists(full_path):
            print(f"[SKIP] Directory exists: {dir_path}")
            skipped_count += 1
        else:
            try:
                os.makedirs(full_path, exist_ok=True)
                print(f"[CREATED] {dir_path}")
                created_count += 1
            except OSError as e:
                print(f"[ERROR] Failed to create {dir_path}: {e}", file=sys.stderr)
                sys.exit(1)

    print(f"\nSetup complete. Created {created_count} directories, skipped {skipped_count}.")

if __name__ == "__main__":
    main()