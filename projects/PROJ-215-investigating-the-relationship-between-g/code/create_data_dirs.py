"""
Script to create required data directories for the project.

This fulfills task T001a: Create data directories `data/raw/`, `data/processed/`,
and `data/interior/`. The script uses the project's path utilities to ensure
the directories exist and logs the actions.
"""
import sys
from llmxive_toolkit import paths, get_logger

# Obtain a logger (writes to console and logs/pipeline.log via get_logger)
log = get_logger(__name__)

def create_directory(relative_path: str) -> None:
    """
    Ensure the directory at the given relative path (relative to the project root)
    exists. Uses the llmxive_toolkit `paths` helper which also creates any missing
    parent directories.
    """
    dir_path = paths.data(relative_path)
    dir_path.mkdir(parents=True, exist_ok=True)
    log.info(f"Created data directory: {dir_path}")

def main() -> None:
    """Create the three required data sub‑directories."""
    for sub_dir in ("raw", "processed", "interior"):
        create_directory(sub_dir)

if __name__ == "__main__":
    # When the script is executed directly, run the creation logic.
    main()
    sys.exit(0)
