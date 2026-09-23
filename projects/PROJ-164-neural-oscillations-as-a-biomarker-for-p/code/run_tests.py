"""
Test Runner for llmXive Project PROJ-164
Executes all unit tests (T010, T011a) and ensures they pass.
"""
import sys
import subprocess
import logging
from pathlib import Path

# Configure logging to capture test output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/pipeline.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    """
    Run pytest on the tests/ directory.
    Exits with code 0 if all tests pass, non-zero otherwise.
    """
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / 'tests'
    
    if not tests_dir.exists():
        logger.error(f"Tests directory not found at {tests_dir}")
        return 1

    logger.info(f"Running unit tests in {tests_dir}...")
    
    # Construct pytest command
    # -v: verbose output
    # --tb=short: short tracebacks
    # --strict-markers: ensure markers are registered
    cmd = [
        sys.executable, '-m', 'pytest',
        str(tests_dir),
        '-v',
        '--tb=short',
        '--color=yes'
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=False, # Stream directly to stdout/stderr for visibility
            text=True
        )
        
        if result.returncode == 0:
            logger.info("SUCCESS: All unit tests passed.")
            return 0
        else:
            logger.error("FAILURE: One or more unit tests failed.")
            logger.error(f"Return code: {result.returncode}")
            return 1
            
    except FileNotFoundError:
        logger.error("pytest not found. Please install it via 'pip install pytest'.")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error running tests: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
