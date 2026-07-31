import logging
from pathlib import Path


def create_dir(path: Path) -> None:
    """Create a directory (including parents) if it does not already exist."""
    path.mkdir(parents=True, exist_ok=True)
    logging.debug("Created directory %s", path)


def create_init_file(dir_path: Path) -> None:
    """Create an empty ``__init__.py`` file inside *dir_path* if it is missing."""
    init_file = dir_path / "__init__.py"
    if not init_file.exists():
        init_file.touch()
        logging.debug("Created __init__.py at %s", init_file)


def main() -> None:
    """Create the required project directory tree."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    required_dirs = [
        Path("data/raw"),
        Path("data/corrupted"),
        Path("code"),
        Path("results"),
        Path("tests"),
    ]

    for d in required_dirs:
        create_dir(d)
        # Ensure package directories have an __init__.py
        if d.name in {"code", "tests"}:
            create_init_file(d)


if __name__ == "__main__":
    main()