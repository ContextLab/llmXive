import os
import sys
import subprocess
import logging
from pathlib import Path

def main():
    """
    Execute pytest on the tests/ directory to ensure all unit and integration tests pass.
    This script serves as the entry point for T043.
    
    Exit codes:
    0: All tests passed
    1: Test execution failed or pytest returned non-zero
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    project_root = Path(__file__).resolve().parent.parent
    tests_dir = project_root / "tests"

    if not tests_dir.exists():
        logger.error(f"Tests directory not found at {tests_dir}")
        sys.exit(1)

    logger.info(f"Running pytest on {tests_dir}...")
    
    # Construct the pytest command
    # -v: verbose output
    # --tb=short: short traceback format
    # --color=yes: ensure color output
    cmd = [
        sys.executable, "-m", "pytest",
        str(tests_dir),
        "-v",
        "--tb=short",
        "--color=yes"
    ]

    try:
        # Run pytest
        result = subprocess.run(
            cmd,
            cwd=project_root,
            check=False,  # We handle the return code manually
            capture_output=False,  # Let output stream to console for visibility
            text=False  # Binary mode for subprocess to handle encoding correctly
        )

        if result.returncode == 0:
            logger.info("All tests passed successfully.")
            sys.exit(0)
        else:
            logger.error(f"Test execution failed with return code {result.returncode}")
            sys.exit(1)

    except FileNotFoundError:
        logger.error("pytest not found. Please install it via: pip install pytest")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error running tests: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()