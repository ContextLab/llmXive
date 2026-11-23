import os
import logging
from pathlib import Path
from typing import List, Optional

# The project uses the utils package namespace for shared utilities
from utils.logger import get_pipeline_logger
from config import get_config


def create_test_directories(
    base_path: Optional[Path] = None,
    subdirs: Optional[List[str]] = None,
) -> List[Path]:
    """
    Create the required test sub‑directories under the repository root.

    Parameters
    ----------
    base_path : Path, optional
        Root directory where the ``tests`` folder resides. If None, uses the
        current working directory.
    subdirs : list of str, optional
        Sub‑directories to create inside ``tests``. Defaults to
        ``["unit", "integration", "contract"]``.

    Returns
    -------
    list[Path]
        Paths that were created (or already existed).
    """
    logger = get_pipeline_logger()
    if base_path is None:
        base_path = Path.cwd()
    tests_root = base_path / "tests"

    if subdirs is None:
        subdirs = ["unit", "integration", "contract"]

    created_paths: List[Path] = []
    for sub in subdirs:
        dir_path = tests_root / sub
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created test directory: {dir_path}")
            created_paths.append(dir_path)
        except Exception as exc:
            logger.error(f"Failed to create test directory {dir_path}: {exc}")
            raise
    return created_paths


def _create_gitkeep_files(base_path: Optional[Path] = None) -> None:
    """
    Populate each test sub‑directory with a ``.gitkeep`` file so that the
    directories are tracked even when they contain no Python modules.
    """
    if base_path is None:
        base_path = Path.cwd()
    for sub in ["unit", "integration", "contract"]:
        keep_path = base_path / "tests" / sub / ".gitkeep"
        try:
            keep_path.touch(exist_ok=True)
        except Exception as exc:
            # Log but do not abort – the directory existence is the primary goal
            get_pipeline_logger().warning(
                f"Could not create .gitkeep at {keep_path}: {exc}"
            )


def main() -> None:
    """
    CLI entry point. Creates the directories and a ``.gitkeep`` file in each.
    """
    create_test_directories()
    _create_gitkeep_files()


if __name__ == "__main__":
    main()
