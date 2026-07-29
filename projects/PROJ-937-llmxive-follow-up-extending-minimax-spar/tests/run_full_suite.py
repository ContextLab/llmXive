"""
Entry point to run the full pytest suite on CPU-only runner.
This script ensures all unit and integration tests pass before proceeding.
"""
import sys
import os
import subprocess
import logging

# Ensure we are running on CPU
os.environ["CUDA_VISIBLE_DEVICES"] = ""

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def run_pytest():
    """Run the full pytest suite."""
    logger.info("Starting full pytest suite on CPU-only runner...")
    
    # Construct the pytest command
    # -v: verbose output
    # --tb=short: short tracebacks
    # --disable-warnings: reduce noise
    # -x: stop on first failure
    # -q: quiet summary at end
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/unit",
        "tests/integration",
        "-v",
        "--tb=short",
        "--disable-warnings",
        "-x",
        "-q"
    ]
    
    logger.info(f"Running command: {' '.join(cmd)}")
    
    try:
        # Run the command
        result = subprocess.run(
            cmd,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            check=True,
            capture_output=False,  # Let output stream to console
            text=True
        )
        
        logger.info("All tests passed successfully!")
        return 0
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Test suite failed with exit code {e.returncode}")
        logger.error("Please review the test failures above.")
        return e.returncode
    except FileNotFoundError:
        logger.error("pytest not found. Please ensure it is installed.")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error running tests: {e}")
        return 1

if __name__ == "__main__":
    exit_code = run_pytest()
    sys.exit(exit_code)