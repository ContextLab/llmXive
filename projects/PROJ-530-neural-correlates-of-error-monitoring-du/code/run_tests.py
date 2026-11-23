"""
Test runner script for PROJ-530-neural-correlates-of-error-monitoring-du.
Executes pytest on all test modules in the tests/ directory.
"""
import os
import sys
import subprocess
import logging
from pathlib import Path

# Add project root to path to ensure imports work if needed
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run pytest on all test modules."""
    tests_dir = project_root / "tests"
    
    if not tests_dir.exists():
        logger.error(f"Tests directory not found at {tests_dir}")
        sys.exit(1)

    logger.info(f"Running pytest on {tests_dir}...")
    
    # Construct pytest command
    # -v: verbose output
    # --tb=short: short tracebacks
    # --color=yes: force color output
    cmd = [
        sys.executable, "-m", "pytest",
        str(tests_dir),
        "-v",
        "--tb=short",
        "--color=yes"
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            check=False,  # We handle the exit code ourselves
            capture_output=False,  # Stream output to console
            text=True
        )

        if result.returncode == 0:
            logger.info("All tests passed successfully.")
            sys.exit(0)
        else:
            logger.error(f"Tests failed with exit code {result.returncode}")
            sys.exit(result.returncode)
            
    except FileNotFoundError:
        logger.error("pytest not found. Please install it: pip install pytest")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
