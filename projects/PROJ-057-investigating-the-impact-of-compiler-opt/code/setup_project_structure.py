import os
import sys

def main():
    """
    Creates the project directory structure for PROJ-057.
    This script executes the mkdir -p logic programmatically to ensure
    the structure exists on disk as required by the task specification.
    """
    # Define the project root relative to the script location or current working directory
    # The task specifies paths relative to the project root.
    # We assume the script is run from the project root or we target the specific project folder.
    project_root = "projects/PROJ-057-investigating-the-impact-of-compiler-opt"
    
    directories = [
        "code/kernels",
        "code/benchmarks",
        "code/analysis",
        "code/utils",
        "data/raw",
        "data/intermediates",
        "data/results",
        "tests/unit",
        "tests/integration"
    ]

    created_count = 0
    for dir_path in directories:
        full_path = os.path.join(project_root, dir_path)
        try:
            os.makedirs(full_path, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        except OSError as e:
            print(f"Error creating directory {full_path}: {e}", file=sys.stderr)
            return 1

    print(f"Successfully created {created_count} directories under {project_root}")
    return 0

if __name__ == "__main__":
    sys.exit(main())