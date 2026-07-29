"""
Lint Check Setup Script for llmXive Pipeline.

This script runs `ruff check` on the `code/` directory to verify
that unused imports have been removed and the code adheres to
style guidelines. It logs the output to `data/processed/lint_log.txt`.
"""
import subprocess
import sys
import logging
from pathlib import Path
from utils.config import get_project_root, get_path, ensure_dir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_ruff_check() -> bool:
    """
    Runs ruff check on the code/ directory.

    Returns:
        bool: True if ruff check passes (exit code 0), False otherwise.
    """
    project_root = get_project_root()
    code_dir = project_root / "code"
    log_path = get_path("data/processed/lint_log.txt")

    # Ensure the log directory exists
    ensure_dir(log_path.parent)

    logger.info(f"Running ruff check on {code_dir}...")

    try:
        # Run ruff check with explicit output to file and capture stdout/stderr
        # Using --output-format=full for detailed logs
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", str(code_dir)],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        # Write the output to the log file
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"Command: ruff check code/\n")
            f.write(f"Exit Code: {result.returncode}\n")
            f.write("-" * 80 + "\n")
            if result.stdout:
                f.write("STDOUT:\n")
                f.write(result.stdout)
            if result.stderr:
                f.write("STDERR:\n")
                f.write(result.stderr)
            f.write("-" * 80 + "\n")

        if result.returncode == 0:
            logger.info("Ruff check passed. No unused imports or style violations found.")
            return True
        else:
            logger.error(f"Ruff check failed with exit code {result.returncode}. See {log_path} for details.")
            return False

    except subprocess.TimeoutExpired:
        logger.error("Ruff check timed out.")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("ERROR: Ruff check timed out.\n")
        return False
    except FileNotFoundError:
        logger.error("Ruff not found. Please install it: pip install ruff")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("ERROR: Ruff not found. Please install it: pip install ruff\n")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"ERROR: {str(e)}\n")
        return False

def main():
    """Main entry point for the lint check script."""
    success = run_ruff_check()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
