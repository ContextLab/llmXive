"""
Setup script to initialize the project directory structure.
Creates all required directories for the statistical analysis pipeline.
"""
import os
import sys

def main():
    # Define the directory structure relative to the project root
    # The script assumes it is run from the project root or adjusts paths accordingly.
    # We will construct paths relative to the script's location to ensure robustness.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # Go up from code/scripts to root

    directories = [
        "data/raw",
        "data/processed",
        "data/checkpoints",
        "code/scripts",      # Already exists as this script is here, but ensures presence
        "code/tests",
        "contracts",
        "paper"
    ]

    created_count = 0
    skipped_count = 0

    print(f"Initializing project structure in: {project_root}")

    for dir_path in directories:
        full_path = os.path.join(project_root, dir_path)
        if os.path.exists(full_path):
            skipped_count += 1
            print(f"  [SKIP] {dir_path} (already exists)")
        else:
            os.makedirs(full_path, exist_ok=True)
            created_count += 1
            print(f"  [CREATE] {dir_path}")

    print(f"\nSetup complete. Created: {created_count}, Skipped: {skipped_count}")

    # Create a .gitkeep file in each directory to ensure they are tracked by git
    # even if empty, which is a common practice in data science projects.
    for dir_path in directories:
        full_path = os.path.join(project_root, dir_path)
        gitkeep_path = os.path.join(full_path, ".gitkeep")
        if not os.path.exists(gitkeep_path):
            with open(gitkeep_path, "w") as f:
                f.write("# Keep this directory in git\n")
            print(f"  [KEEP] {os.path.join(dir_path, '.gitkeep')}")

    return 0

if __name__ == "__main__":
    sys.exit(main())