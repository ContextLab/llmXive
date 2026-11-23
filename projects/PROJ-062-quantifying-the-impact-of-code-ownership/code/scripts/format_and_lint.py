import subprocess
import sys
import argparse
from pathlib import Path
from utils.logging_utils import get_logger

logger = get_logger(__name__)

def run_command(cmd: list) -> bool:
    """Run a command and return success status."""
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Format and lint the project code.")
    parser.add_argument("--fix", action="store_true", help="Fix formatting issues with black.")
    parser.add_argument("--check", action="store_true", help="Only check formatting and linting (default).")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    tests_dir = project_root / "tests"

    if args.fix:
        logger.info("Fixing formatting with black...")
        success = run_command([sys.executable, "-m", "black", str(code_dir), str(tests_dir)])
        if success:
            logger.info("Formatting fixed successfully.")
        else:
            logger.error("Failed to fix formatting.")
            sys.exit(1)
    
    logger.info("Running flake8...")
    flake8_success = run_command([sys.executable, "-m", "flake8", str(code_dir), str(tests_dir)])
    
    if not flake8_success:
        logger.error("flake8 found issues. Please fix them manually.")
        sys.exit(1)

    logger.info("Running black check...")
    black_success = run_command([sys.executable, "-m", "black", "--check", str(code_dir), str(tests_dir)])
    
    if not black_success:
        logger.error("black found formatting issues. Run with --fix to fix them.")
        sys.exit(1)

    logger.info("All linting and formatting checks passed.")
    sys.exit(0)

if __name__ == "__main__":
    main()