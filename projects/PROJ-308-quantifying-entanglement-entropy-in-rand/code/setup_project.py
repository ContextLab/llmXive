"""
Project initialization script for PROJ-308-quantifying-entanglement-entropy-in-rand.
Creates the required directory structure and verification artifacts.
"""
import os
import sys
from pathlib import Path


def create_directory_structure(base_path: str = None) -> bool:
    """
    Creates the full directory structure required for the project.

    Args:
        base_path: The root directory for the project. Defaults to
                   'projects/PROJ-308-quantifying-entanglement-entropy-in-rand'
                   relative to the current working directory.

    Returns:
        True if all directories were created successfully, False otherwise.
    """
    if base_path is None:
        # Determine the project root relative to the script location or cwd
        # The task specifies the path relative to project root
        base_path = "projects/PROJ-308-quantifying-entanglement-entropy-in-rand"

    root = Path(base_path)
    root.mkdir(parents=True, exist_ok=True)

    # Define all required directories relative to root
    directories = [
        "code",
        "data",
        "state",
        "tests",
        "docs",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "state/projects",
        "tools",
        "reviews"
    ]

    created_count = 0
    failed_dirs = []

    for dir_path in directories:
        full_path = root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
        except OSError as e:
            print(f"Error creating directory {full_path}: {e}", file=sys.stderr)
            failed_dirs.append(str(full_path))

    if failed_dirs:
        print(f"Failed to create {len(failed_dirs)} directories.", file=sys.stderr)
        return False

    print(f"Successfully created {created_count} directories under {root}.")
    return True


def write_setup_log(base_path: str = None, log_filename: str = "setup_log.txt") -> None:
    """
    Writes a verification log file confirming the directory structure.

    Args:
        base_path: The root directory for the project.
        log_filename: The name of the log file to create.
    """
    if base_path is None:
        base_path = "projects/PROJ-308-quantifying-entanglement-entropy-in-rand"

    root = Path(base_path)
    log_path = root / log_filename

    # List all expected directories to verify
    expected_dirs = [
        "code", "data", "state", "tests", "docs",
        "data/raw", "data/processed",
        "tests/unit", "tests/integration",
        "state/projects", "tools", "reviews"
    ]

    with open(log_path, 'w') as f:
        f.write(f"Setup Log for {root}\n")
        f.write("=" * 40 + "\n")
        f.write(f"Status: SUCCESS\n")
        f.write(f"Directories verified:\n")
        for d in expected_dirs:
            full_path = root / d
            if full_path.is_dir():
                f.write(f"  [OK] {d}\n")
            else:
                f.write(f"  [FAIL] {d}\n")
        f.write("=" * 40 + "\n")
        f.write("Verification complete.\n")

    print(f"Setup log written to {log_path}")


def main():
    """
    Entry point for the script.
    Creates directories and generates the setup log.
    """
    # Default project path as per task specification
    project_root = "projects/PROJ-308-quantifying-entanglement-entropy-in-rand"

    print(f"Initializing project structure at: {project_root}")

    success = create_directory_structure(project_root)

    if success:
        write_setup_log(project_root)
        print("Project initialization complete.")
        sys.exit(0)
    else:
        print("Project initialization failed due to directory creation errors.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
