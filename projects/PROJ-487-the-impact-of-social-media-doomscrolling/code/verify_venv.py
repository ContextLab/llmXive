import os
import sys
from pathlib import Path
import stat
from utils.logging import get_logger

def verify_venv(project_root: Path) -> bool:
    """
    Verify that the virtual environment activation script exists and is executable.

    Args:
        project_root: Path to the project root directory.

    Returns:
        True if the venv is valid and executable, False otherwise.
    """
    logger = get_logger()
    activate_path = project_root / "venv" / "bin" / "activate"

    if not activate_path.exists():
        logger.error(f"Virtual environment activation script not found: {activate_path}")
        return False

    # Check if file is executable (Unix-like systems)
    file_stat = activate_path.stat()
    is_executable = bool(file_stat.st_mode & stat.S_IEXEC)

    # On Windows, we check for existence primarily, as .bat files aren't "executable" in the same way
    # but the task specifically asks for `venv/bin/activate` which implies a Unix-style venv structure.
    # If running on Windows, the path would be `venv/Scripts/activate`.
    # We will strictly check the requested path `venv/bin/activate`.
    
    if not is_executable:
        # Try to make it executable if permissions allow
        try:
            os.chmod(activate_path, file_stat.st_mode | stat.S_IEXEC)
            logger.info(f"Set execute permission on: {activate_path}")
            is_executable = True
        except PermissionError:
            logger.warning(f"Could not set execute permission on: {activate_path}")
            # On some systems (e.g., FAT32), this might fail but the file might still work
            # We will treat it as a warning but continue if the file exists.
            # However, strict compliance requires it to be executable.
            return False

    logger.info(f"Virtual environment activation script verified: {activate_path}")
    return True

def main() -> int:
    """Main entry point for the script."""
    logger = get_logger()
    logger.info("Starting virtual environment verification...")

    # Determine project root (assume script is in code/ directory)
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent

    if verify_venv(project_root):
        logger.info("Virtual environment verification PASSED.")
        return 0
    else:
        logger.error("Virtual environment verification FAILED.")
        logger.error("Ensure T004a has been run successfully in the project root.")
        return 1

if __name__ == "__main__":
    sys.exit(main())