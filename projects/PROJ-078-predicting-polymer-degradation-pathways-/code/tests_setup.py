import os
import sys
from pathlib import Path
from utils import get_logger

def verify_test_structure():
    """
    Verifies that the pytest directory structure exists.
    Creates tests/unit and tests/integration if they are missing.
    Returns True if structure is valid, False otherwise.
    """
    logger = get_logger()
    root_dir = Path(__file__).resolve().parent.parent
    tests_dir = root_dir / "tests"
    unit_dir = tests_dir / "unit"
    integration_dir = tests_dir / "integration"

    try:
        # Ensure tests directory exists
        if not tests_dir.exists():
            logger.info(f"Creating tests directory: {tests_dir}")
            tests_dir.mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py to make it a package
        (tests_dir / "__init__.py").touch(exist_ok=True)

        # Ensure unit directory exists
        if not unit_dir.exists():
            logger.info(f"Creating unit tests directory: {unit_dir}")
            unit_dir.mkdir(parents=True, exist_ok=True)
        (unit_dir / "__init__.py").touch(exist_ok=True)

        # Ensure integration directory exists
        if not integration_dir.exists():
            logger.info(f"Creating integration tests directory: {integration_dir}")
            integration_dir.mkdir(parents=True, exist_ok=True)
        (integration_dir / "__init__.py").touch(exist_ok=True)

        # Verify structure
        if not all([
            tests_dir.exists(),
            unit_dir.exists(),
            integration_dir.exists(),
            (unit_dir / "__init__.py").exists(),
            (integration_dir / "__init__.py").exists()
        ]):
            logger.error("Test structure verification failed.")
            return False

        logger.info("Test directory structure verified successfully.")
        return True

    except Exception as e:
        logger.error(f"Error verifying test structure: {e}")
        return False

def main():
    """Main entry point for T008 setup."""
    logger = get_logger()
    logger.info("Starting T008: Setup pytest framework and directory structure")
    
    success = verify_test_structure()
    
    if success:
        logger.info("T008 completed successfully.")
        return 0
    else:
        logger.error("T008 failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
