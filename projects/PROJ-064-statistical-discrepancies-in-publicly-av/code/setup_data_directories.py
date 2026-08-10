"""
T004: Setup data directory structure.

Creates the required directory hierarchy for the statistical discrepancies project:
- data/raw/
- data/processed/
- state/ (for checksums and intermediate state)

This script is idempotent and will not fail if directories already exist.
"""
import os
from pathlib import Path

def setup_data_directories(project_root: Path) -> None:
    """
    Create the standard data and state directories relative to the project root.

    Args:
        project_root: The root path of the project (e.g., projects/PROJ-064-...)
    """
    # Define the required directories relative to the project root
    directories = [
        "data/raw",
        "data/processed",
        "state"
    ]

    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        # Optional: Create a .gitkeep to ensure directories are tracked by git
        # if they are empty, though the project might handle this elsewhere.
        gitkeep = full_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text(f"# Keep directory structure for {dir_path}\n")

    print(f"Successfully created data directories in: {project_root}")

if __name__ == "__main__":
    # Determine project root: assuming script is in code/
    # and project root is the parent of code/
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent

    setup_data_directories(project_root)
