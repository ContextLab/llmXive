import os
from pathlib import Path

def main():
    """Create the required artifacts directory structure."""
    # Determine the project root. Assuming this script is in code/,
    # the project root is the parent directory.
    project_root = Path(__file__).resolve().parent.parent

    # Define the artifact subdirectories to be created
    artifact_dirs = [
        "artifacts/models",
        "artifacts/reports",
        "artifacts/figures"
    ]

    created_paths = []

    for dir_path in artifact_dirs:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        created_paths.append(str(full_path))
        print(f"Created directory: {full_path}")

    return created_paths

if __name__ == "__main__":
    main()