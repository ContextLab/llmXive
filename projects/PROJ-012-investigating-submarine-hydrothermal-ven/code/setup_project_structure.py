"""T001: Create the project directory structure per the implementation plan.

Creates the required directories (with .gitkeep placeholders so empty
directories persist in version control):
    data/raw/
    data/processed/
    code/
    tests/
    state/
    results/figures/

Running this script is idempotent: existing directories are left intact.
"""

import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_DIRECTORIES = [
    "data/raw",
    "data/processed",
    "code",
    "tests",
    "state",
    "results/figures",
]


def create_project_structure(root: Path = PROJECT_ROOT) -> None:
    """Create all required project directories under `root`.

    Args:
        root: Project root directory (defaults to this file's parent's parent).
    """
    for rel_path in REQUIRED_DIRECTORIES:
        directory = root / rel_path
        directory.mkdir(parents=True, exist_ok=True)
        gitkeep = directory / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("")
            logger.info("Created directory: %s", directory)
        else:
            logger.info("Directory already exists: %s", directory)


def verify_project_structure(root: Path = PROJECT_ROOT) -> bool:
    """Verify that every required directory exists.

    Args:
        root: Project root directory.

    Returns:
        True if all required directories exist, False otherwise.
    """
    missing = [
        rel
        for rel in REQUIRED_DIRECTORIES
        if not (root / rel).is_dir()
    ]
    if missing:
        logger.error("Missing directories: %s", missing)
        return False
    logger.info(
        "Project structure verified: %s", REQUIRED_DIRECTORIES
    )
    return True


def main() -> int:
    create_project_structure()
    if verify_project_structure():
        logger.info("T001 complete: project structure in place.")
        return 0
    logger.error("T001 FAILED: project structure incomplete.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())