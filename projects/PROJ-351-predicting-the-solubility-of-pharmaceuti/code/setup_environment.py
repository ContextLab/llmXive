"""
Environment setup and validation script.
Verifies Python version and checks for installed dependencies.
"""
import sys
import importlib
import logging
from typing import List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

REQUIRED_PYTHON_VERSION = (3, 10)

def check_python_version() -> bool:
    """Check if the current Python version meets the minimum requirement."""
    current_version = sys.version_info
    if current_version < REQUIRED_PYTHON_VERSION:
        logger.error(
            f"Python version {current_version.major}.{current_version.minor} "
            f"is not supported. Requires Python >= {REQUIRED_PYTHON_VERSION[0]}.{REQUIRED_PYTHON_VERSION[1]}."
        )
        return False
    logger.info(f"Python version {current_version.major}.{current_version.minor} verified.")
    return True

def check_dependencies() -> Tuple[bool, List[str]]:
    """Check if all required dependencies are installed."""
    missing_packages = []
    packages_to_check = [
        'rdkit', 'pandas', 'numpy', 'scipy', 'sklearn', 'torch', 'torch_geometric', 'matplotlib'
    ]

    for package in packages_to_check:
        try:
            importlib.import_module(package)
            logger.debug(f"Package '{package}' found.")
        except ImportError:
            missing_packages.append(package)
            logger.warning(f"Package '{package}' is missing.")

    if missing_packages:
        logger.error(
            f"Missing dependencies: {', '.join(missing_packages)}. "
            "Please run: pip install -r requirements.txt"
        )
        return False, missing_packages

    logger.info("All dependencies verified.")
    return True, []

def main():
    """Main entry point for environment validation."""
    logger.info("Starting environment validation...")

    if not check_python_version():
        sys.exit(1)

    success, missing = check_dependencies()
    if not success:
        sys.exit(1)

    logger.info("Environment validation complete. Project ready.")

if __name__ == "__main__":
    main()
