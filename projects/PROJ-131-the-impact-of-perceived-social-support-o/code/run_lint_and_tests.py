"""
Lint and Test Runner.

Implements T063: Run ruff and pytest.
"""
import os
import sys
import subprocess
import time
from pathlib import Path

# Add project root
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_command(cmd: list, name: str):
    logger = logging.getLogger(__name__)
    logger.info(f"Running {name}: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=project_root.parent, capture_output=True, text=True, check=True)
        logger.info(f"{name} passed.")
        if result.stdout:
            logger.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"{name} failed: {e}")
        if e.stdout:
            logger.error(e.stdout)
        if e.stderr:
            logger.error(e.stderr)
        return False

def main():
    """Runs linter and tests."""
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Lint and Test Run (T063)...")
    
    # Run Ruff
    ruff_ok = run_command(["ruff", "check", "."], "Ruff")
    
    # Run Pytest
    pytest_ok = run_command(["pytest", "tests/", "-v"], "Pytest")
    
    if ruff_ok and pytest_ok:
        logger.info("All checks passed.")
    else:
        logger.error("Some checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
