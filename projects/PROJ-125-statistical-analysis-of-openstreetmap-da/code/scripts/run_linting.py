"""
Linting and auto-fix script for the project.
Runs ruff and black on the code/ directory and verifies no errors remain.
"""
import subprocess
import sys
from pathlib import Path
from utils.logging import get_logger

logger = get_logger(__name__)

def run_command(cmd: list[str], description: str) -> bool:
    """Run a shell command and return True if successful."""
    logger.info(f"Running: {description}")
    logger.info(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            cwd=Path(__file__).parent.parent.parent
        )
        if result.returncode == 0:
            logger.info(f"✓ {description} completed successfully.")
            return True
        else:
            logger.error(f"✗ {description} failed.")
            if result.stdout:
                logger.error(f"STDOUT:\n{result.stdout}")
            if result.stderr:
                logger.error(f"STDERR:\n{result.stderr}")
            return False
    except Exception as e:
        logger.error(f"✗ {description} raised exception: {e}")
        return False

def main() -> int:
    """Main entry point for linting script."""
    logger.info("Starting linting and auto-fix process...")

    project_root = Path(__file__).parent.parent.parent
    code_dir = project_root / "code"

    if not code_dir.exists():
        logger.error(f"Code directory not found: {code_dir}")
        return 1

    # Step 1: Run ruff check (with fixes)
    # Using ruff check --fix to auto-fix issues where possible
    ruff_check_success = run_command(
        ["ruff", "check", "--fix", str(code_dir)],
        "Ruff check with auto-fix"
    )

    # Step 2: Run ruff format (or black if ruff format not available)
    # Ruff format is the modern replacement for black
    ruff_format_success = run_command(
        ["ruff", "format", str(code_dir)],
        "Ruff format (black replacement)"
    )

    # Step 3: Run final ruff check to ensure no errors remain
    logger.info("Running final verification...")
    final_check_success = run_command(
        ["ruff", "check", str(code_dir)],
        "Final ruff check (no fixes)"
    )

    if ruff_check_success and ruff_format_success and final_check_success:
        logger.info("✓ All linting checks passed. Code is clean.")
        return 0
    else:
        logger.error("✗ Linting failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
