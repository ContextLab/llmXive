import os
import sys
from pathlib import Path
from utils import get_logger

def verify_test_structure():
    """Verify that the pytest directory structure is correctly set up."""
    logger = get_logger(__name__)
    root = Path(__file__).parent.parent

    required_dirs = [
        root / "tests",
        root / "tests" / "unit",
        root / "tests" / "integration",
    ]

    all_ok = True
    for dir_path in required_dirs:
        if not dir_path.exists():
            logger.error(f"Missing directory: {dir_path}")
            all_ok = False
        else:
            logger.info(f"Found directory: {dir_path}")

    # Check for conftest.py
    conftest = root / "tests" / "conftest.py"
    if not conftest.exists():
        logger.error(f"Missing conftest.py: {conftest}")
        all_ok = False
    else:
        logger.info(f"Found conftest.py: {conftest}")

    # Check for pytest.ini
    pytest_ini = root / "tests" / "pytest.ini"
    if not pytest_ini.exists():
        logger.error(f"Missing pytest.ini: {pytest_ini}")
        all_ok = False
    else:
        logger.info(f"Found pytest.ini: {pytest_ini}")

    if all_ok:
        logger.info("Test structure verification passed.")
    else:
        logger.error("Test structure verification failed.")
        sys.exit(1)

def main():
    verify_test_structure()

if __name__ == "__main__":
    main()
