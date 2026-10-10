import os
import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Optional

def create_directory_structure(project_root: Path) -> List[Path]:
    """
    Creates the required directory structure for the molecular toxicity project.

    Args:
        project_root: The root directory of the project (e.g., .../PROJ-356-predicting-molecular-toxicity-from-struc)

    Returns:
        List of created directory paths.
    """
    # Define the relative paths to create
    relative_paths = [
        "code",
        "code/src",
        "code/tests",
        "code/data",
        "code/data/raw",
        "code/data/processed",
        "code/results",
        "code/models",
        "code/config",
        "code/docs",
        "code/scripts",
        "code/state",
        "code/specs/001-predicting-molecular-toxicity-from-struc/contracts"
    ]

    created_dirs = []
    for rel_path in relative_paths:
        full_path = project_root / rel_path
        full_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(full_path)
        print(f"Created directory: {full_path}")

    return created_dirs

def verify_structure(project_root: Path, required_dirs: List[str]) -> Tuple[bool, List[str]]:
    """
    Verifies that all required directories exist.

    Args:
        project_root: The root directory of the project.
        required_dirs: List of relative directory paths to check.

    Returns:
        Tuple of (success: bool, missing_dirs: List[str])
    """
    missing = []
    for rel_path in required_dirs:
        full_path = project_root / rel_path
        if not full_path.exists():
            missing.append(rel_path)
        elif not full_path.is_dir():
            missing.append(rel_path)

    if missing:
        print(f"Verification FAILED. Missing directories: {missing}")
        return False, missing
    else:
        print("Verification SUCCESS. All required directories exist.")
        return True, []

def main():
    parser = argparse.ArgumentParser(
        description="Initialize the project directory structure for molecular toxicity prediction."
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default="projects/PROJ-356-predicting-molecular-toxicity-from-struc",
        help="Path to the project root directory. Default: projects/PROJ-356-predicting-molecular-toxicity-from-struc"
    )

    args = parser.parse_args()
    project_root = Path(args.project_root)

    # Ensure the project root itself exists
    if not project_root.exists():
        print(f"Creating project root: {project_root}")
        project_root.mkdir(parents=True, exist_ok=True)

    print(f"Initializing project structure at: {project_root}")

    # Create directories
    created = create_directory_structure(project_root)

    # Verify
    required = [
        "code", "code/src", "code/tests", "code/data", "code/data/raw",
        "code/data/processed", "code/results", "code/models", "code/config",
        "code/docs", "code/scripts", "code/state",
        "code/specs/001-predicting-molecular-toxicity-from-struc/contracts"
    ]

    success, missing = verify_structure(project_root, required)

    if not success:
        sys.exit(1)

    print("Project initialization complete.")

if __name__ == "__main__":
    main()