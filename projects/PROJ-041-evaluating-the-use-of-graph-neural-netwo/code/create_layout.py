"""
create_layout.py
----------------

Creates the core project layout and essential utility files.
Ensures that the directories `code/`, `data/`, `docs/`, and `tests/` exist,
copies the top‑level `requirements.txt` and `pyproject.toml` into the `code/`
directory, and creates a minimal configuration file.
"""

from pathlib import Path
from llmxive_toolkit import get_logger

log = get_logger(__name__)

def _ensure_dirs():
    """Create the main project directories."""
    for d in ["code", "data", "docs", "tests"]:
        p = Path(d)
        p.mkdir(parents=True, exist_ok=True)
        log.info("Ensured directory %s", p)

    # utils subdirectory inside code
    utils_path = Path("code/utils")
    utils_path.mkdir(parents=True, exist_ok=True)
    log.info("Ensured utils directory %s", utils_path)

def _copy_root_file(root_name: str, target_dir: Path):
    """Copy a file from the repository root into the target directory."""
    root_path = Path(root_name)
    target_path = target_dir / root_name
    if not root_path.is_file():
        raise RuntimeError(f"Root file {root_name!r} not found.")
    target_path.write_text(root_path.read_text())
    log.info("Copied %s to %s", root_path, target_path)

def _create_config():
    """Create a minimal configuration file if it does not exist."""
    config_path = Path("code/config.yaml")
    if not config_path.exists():
        config_path.write_text("active_dataset: null\n")
        log.info("Created placeholder config %s", config_path)
    else:
        log.info("Config %s already exists", config_path)

def main() -> None:
    """Entry point for the layout‑creation script."""
    log.info("Starting project layout creation")
    _ensure_dirs()
    _copy_root_file("requirements.txt", Path("code"))
    _copy_root_file("pyproject.toml", Path("code"))
    _create_config()
    log.info("Project layout creation completed successfully")

if __name__ == "__main__":
    main()
