"""
Script to create required data sub‑directories for the project.

Directories created:
  - data/raw/
  - data/processed/
  - data/interior/

The script uses the project's ``llmxive_toolkit.paths`` helper which
automatically creates any missing parent directories and returns a
``pathlib.Path`` object. Logging is performed via ``llmxive_toolkit.get_logger``.
Running the script as a module (``python code/create_data_dirs.py``) will
create the directories and exit with status 0.
"""

from llmxive_toolkit import paths, get_logger

# Obtain a logger that writes to the standard pipeline log file.
log = get_logger(__name__)

def create_directory(relative_path: str) -> None:
    """
    Ensure a data sub‑directory exists.

    Parameters
    ----------
    relative_path : str
        Relative path under the project's ``data`` folder (e.g. ``"raw"``).
    """
    # ``paths.data`` creates the folder hierarchy under ``data/``.
    dir_path = paths.data(relative_path)
    dir_path.mkdir(parents=True, exist_ok=True)
    log.info(f"Created data directory: {dir_path}")

def main() -> None:
    """
    Create the three required data directories.
    """
    for sub_dir in ("raw", "processed", "interior"):
        create_directory(sub_dir)

if __name__ == "__main__":
    main()