"""
Script to initialize the full project structure including data and artifacts directories.
This is a helper to ensure T001, T002, and T003 are satisfied in one go if needed,
though T003 specifically targets the artifacts folder.
"""
import os
from pathlib import Path


def main():
    """Create all required project directories."""
    # Determine project root
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    # Directories for T001
    root_dirs = [
        project_root / "code",
        project_root / "tests",
        project_root / "data",
        project_root / "artifacts",
    ]

    # Directories for T002
    data_subdirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "split",
    ]

    # Directories for T003
    artifact_subdirs = [
        project_root / "artifacts" / "models",
        project_root / "artifacts" / "reports",
        project_root / "artifacts" / "figures",
    ]

    all_dirs = root_dirs + data_subdirs + artifact_subdirs

    for dir_path in all_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        gitkeep_path = dir_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
        print(f"Ensured: {dir_path}")

    print("Project structure setup complete.")


if __name__ == "__main__":
    main()