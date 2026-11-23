"""
Virtual Environment Verification Utility.

This script verifies that the virtual environment activation script exists
and is executable, as required by task T004b.
"""
import os
import sys
import stat
from pathlib import Path
from utils.logging import get_logger

def verify_venv(project_root: Path) -> bool:
    """
    Verify that the venv activation script exists and is executable.

    Args:
        project_root: Path to the project root directory.

    Returns:
        True if verification passes, False otherwise.
    """
    logger = get_logger(__name__)
    venv_activate_path = project_root / "venv" / "bin" / "activate"

    # Check if file exists
    if not venv_activate_path.exists():
        logger.error(f"Virtual environment activation script not found: {venv_activate_path}")
        logger.error("Please run 'python -m venv venv' in the project root first (Task T004a).")
        return False

    # Check if file is executable
    file_stat = venv_activate_path.stat()
    is_executable = bool(file_stat.st_mode & stat.S_IEXEC)

    if not is_executable:
        logger.error(f"Activation script exists but is not executable: {venv_activate_path}")
        logger.error("Please run 'chmod +x venv/bin/activate' to fix permissions.")
        return False

    logger.info(f"Virtual environment activation script verified: {venv_activate_path}")
    logger.info("Permissions: OK (executable)")
    return True

def main() -> int:
    """
    Main entry point for the verification script.

    Returns:
        Exit code: 0 for success, 1 for failure.
    """
    logger = get_logger(__name__)
    logger.info("Starting virtual environment verification (Task T004b)...")

    # Determine project root (assuming script is run from project root or code/utils/)
    current_path = Path(__file__).resolve()
    # Navigate up two levels from code/utils/ to project root
    project_root = current_path.parent.parent.parent

    if verify_venv(project_root):
        logger.info("Virtual environment verification PASSED.")
        return 0
    else:
        logger.error("Virtual environment verification FAILED.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
