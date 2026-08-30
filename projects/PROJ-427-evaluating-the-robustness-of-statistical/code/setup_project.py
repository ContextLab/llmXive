"""
Setup script for creating the required project directory structure and
initializing package markers.

This script is idempotent; running it multiple times will not raise errors
and will ensure the expected directories and ``__init__.py`` files exist.
"""

import logging
from pathlib import Path

# Configure a very small logger – the calling context can adjust as needed.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_dir(dir_path: Path) -> None:
    """
    Create a directory (including any missing parent directories).

    Parameters
    ----------
    dir_path: Path
        The directory to create.
    """
    if not isinstance(dir_path, Path):
        dir_path = Path(dir_path)
    dir_path.mkdir(parents=True, exist_ok=True)
    logger.debug("Created directory: %s", dir_path)

def create_init_file(package_dir: Path) -> None:
    """
    Ensure an ``__init__.py`` file exists in the given package directory.

    Parameters
    ----------
    package_dir: Path
        Directory that should become a Python package.
    """
    if not isinstance(package_dir, Path):
        package_dir = Path(package_dir)
    init_path = package_dir / "__init__.py"
    init_path.touch(exist_ok=True)
    logger.debug("Ensured __init__.py at: %s", init_path)

def main() -> None:
    """
    Create the full project tree required by the specification:

    - data/raw
    - data/corrupted
    - code
    - results
    - tests

    It also creates empty ``__init__.py`` files in the ``code`` and ``tests``
    directories so they are recognised as Python packages.
    """
    # Base directories relative to the repository root
    base_paths = {
        "data_raw": Path("data/raw"),
        "data_corrupted": Path("data/corrupted"),
        "code_dir": Path("code"),
        "results_dir": Path("results"),
        "tests_dir": Path("tests"),
    }

    # Create each directory
    for name, path in base_paths.items():
        create_dir(path)
        logger.info("Directory created (or already existed): %s", path)

    # Create package markers
    create_init_file(base_paths["code_dir"])
    create_init_file(base_paths["tests_dir"])
    logger.info("Empty __init__.py files created in 'code' and 'tests' packages.")

if __name__ == "__main__":
    main()
