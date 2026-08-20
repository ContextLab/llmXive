"""
Environment setup and verification script.
Checks that all required dependencies are installed and compatible.
"""
import sys
import importlib
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

REQUIRED_PACKAGES = {
    'torch': '2.1.0',
    'numpy': '1.26.2',
    'scipy': '1.11.4',
    'pytest': '7.4.3',
    'psutil': '5.9.6',
    'yaml': '6.0.1',
}

def check_import(package_name: str, min_version: str = None) -> bool:
    """
    Check if a package is installed and optionally verify version.

    Args:
        package_name: Name of the package to check
        min_version: Optional minimum version string (e.g., '2.1.0')

    Returns:
        True if package is installed and meets version requirement, False otherwise
    """
    try:
        module = importlib.import_module(package_name)
        logger.info(f"✓ {package_name} is installed")

        if min_version:
            if hasattr(module, '__version__'):
                version = module.__version__
                logger.info(f"  Version: {version}")
                # Simple version comparison (assumes semantic versioning)
                if _version_gte(version, min_version):
                    logger.info(f"  ✓ Version {version} >= {min_version}")
                    return True
                else:
                    logger.error(f"  ✗ Version {version} < {min_version}")
                    return False
            else:
                logger.warning(f"  ! {package_name} has no __version__ attribute")
                return True
        return True
    except ImportError as e:
        logger.error(f"✗ {package_name} is NOT installed: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Error checking {package_name}: {e}")
        return False

def _version_gte(current: str, minimum: str) -> bool:
    """
    Check if current version is greater than or equal to minimum version.

    Args:
        current: Current version string (e.g., '2.1.0')
        minimum: Minimum required version string

    Returns:
        True if current >= minimum
    """
    def parse_version(v: str) -> tuple:
        """Parse version string into tuple of integers."""
        parts = v.split('.')
        return tuple(int(p) for p in parts if p.isdigit())

    try:
        current_tuple = parse_version(current)
        minimum_tuple = parse_version(minimum)
        return current_tuple >= minimum_tuple
    except (ValueError, AttributeError):
        # If parsing fails, assume versions are compatible
        return True

def main():
    """
    Main entry point for environment verification.

    Checks all required packages and exits with appropriate code:
    - 0: All checks passed
    - 1: One or more checks failed
    """
    logger.info("Starting environment verification...")
    logger.info(f"Python version: {sys.version}")

    all_passed = True

    for package, version in REQUIRED_PACKAGES.items():
        if not check_import(package, version):
            all_passed = False

    if all_passed:
        logger.info("\n✓ All required packages are installed and compatible.")
        logger.info("Environment is ready for execution.")
        return 0
    else:
        logger.error("\n✗ One or more required packages are missing or incompatible.")
        logger.error("Please install the missing packages using:")
        logger.error("  pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    sys.exit(main())
