"""
create_data_folders.py

Script to create the required data directory structure for the project:
- data/raw/
- data/processed/
- data/validation/
- data/results/
- results/  (legacy top‑level results folder used by some existing scripts)

The script uses the llmxive_toolkit `paths` helper which creates the parent
directories automatically when constructing a Path. We explicitly call
``mkdir`` with ``parents=True`` and ``exist_ok=True`` to make the operation
idempotent.

It can be run directly (`python code/create_data_folders.py`) or imported
and the ``create_folders`` function called from tests or other code.
"""

from pathlib import Path
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _ensure_dir(p: Path) -> Path:
    """
    Ensure that the directory ``p`` exists.

    Parameters
    ----------
    p : Path
        Directory path to create.

    Returns
    -------
    Path
        The same Path instance (for convenience).
    """
    try:
        p.mkdir(parents=True, exist_ok=True)
        log.info(f"Created/verified directory: {p}")
    except Exception as exc:
        log.error(f"Failed to create directory {p}: {exc}")
        raise
    return p

def create_folders() -> list[Path]:
    """
    Create the required data directories (including the legacy ``results/``).

    Returns
    -------
    list[Path]
        List of the directory Paths that were created or verified.
    """
    dirs = [
        paths.data("raw"),
        paths.data("processed"),
        paths.data("validation"),
        paths.data("results"),   # <-- new required folder under ``data/``
        paths.results(""),       # legacy top‑level ``results/`` folder
    ]
    created = [_ensure_dir(d) for d in dirs]
    return created

def main() -> None:
    """
    Entry point for the script when executed from the command line.
    """
    created_dirs = create_folders()
    log.info("Data directory structure ready.")
    for d in created_dirs:
        log.debug(f"Directory: {d}")

if __name__ == "__main__":
    main()