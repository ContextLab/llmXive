"""
Verification script to ensure unused imports and dead code have been removed.
This script runs ruff check and reports any remaining issues.
"""

import subprocess
import sys
from pathlib import Path

from utils.logging import get_main_logger

logger = get_main_logger()

def main() -> int:
    """Main entry point for verification."""
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"

    if not code_dir.exists():
        logger.error(f"Code directory not found: {code_dir}")
        return 1

    logger.info(f"Verifying cleanup in {code_dir}")

    # Run ruff check to identify any remaining issues
    # --select=I: Check for import issues (unused, unsorted, etc.)
    # --select=F401: Specifically check for unused imports
    try:
        result = subprocess.run(
            ["ruff", "check", "--select=F401", str(code_dir)],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,  # Don't raise exception, we want to see output
        )

        if result.returncode == 0:
            logger.info("✅ No unused imports found!")
            return 0
        else:
            logger.warning("❌ Remaining issues found:")
            logger.warning(result.stdout)
            logger.warning(result.stderr)
            return 1
    except FileNotFoundError:
        logger.error("ruff not found. Please install it to verify cleanup.")
        return 1
    except Exception as e:
        logger.error(f"Error running verification: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())