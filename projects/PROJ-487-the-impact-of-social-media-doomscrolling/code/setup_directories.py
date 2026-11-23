import os
import sys
from pathlib import Path
import logging
from utils.logging import get_logger

def create_code_directories(base_path: Path, logger: logging.Logger) -> bool:
    """
    Create the required code directories: code/data/, code/tests/, code/utils/
    relative to the project root.

    Args:
        base_path: The project root path (projects/PROJ-487-...)
        logger: The configured logger instance.

    Returns:
        True if all directories were created or already exist, False otherwise.
    """
    code_dirs = [
        base_path / "code" / "data",
        base_path / "code" / "tests",
        base_path / "code" / "utils",
    ]

    success = True
    for dir_path in code_dirs:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directory created or verified: {dir_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            success = False

    return success

def main():
    """
    Main entry point for T003: Create code directories.
    Assumes the project root is `projects/PROJ-487-the-impact-of-social-media-doomscrolling`.
    """
    logger = get_logger(__name__)
    logger.info("Starting T003: Create code directories")

    # Determine project root based on the task description
    # The task specifies: projects/PROJ-487-the-impact-of-social-media-doomscrolling/
    project_root = Path("projects/PROJ-487-the-impact-of-social-media-doomscrolling")

    if not project_root.exists():
        logger.error(f"Project root {project_root} does not exist. Run T001 first.")
        sys.exit(1)

    success = create_code_directories(project_root, logger)

    if success:
        logger.info("T003 completed successfully: code directories created.")
        # Verify existence explicitly for the task requirement
        required_dirs = [
            project_root / "code" / "data",
            project_root / "code" / "tests",
            project_root / "code" / "utils",
        ]
        for d in required_dirs:
            if not d.is_dir():
                logger.error(f"Verification failed: {d} is not a directory.")
                sys.exit(1)
        logger.info("Verification passed: All required directories exist.")
    else:
        logger.error("T003 failed: Some directories could not be created.")
        sys.exit(1)

if __name__ == "__main__":
    main()
