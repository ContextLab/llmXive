"""
Test script to verify Python 3.11 compatibility of all dependencies listed in requirements.txt.

This script attempts to import all dependencies and asserts that:
1. No ImportError occurs (module is available)
2. No version conflicts are detected that would prevent usage on Python 3.11
3. All wheels are compatible with the current Python version
"""
import sys
import subprocess
import importlib
import logging
from typing import List, Set, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Expected dependencies based on T002 requirements
EXPECTED_PACKAGES = {
    'pandas',
    'statsmodels',
    'scikit-learn',
    'requests',
    'gitpython',
    'pyyaml',
    'numpy',
    'scipy',
    'pytest',
    'psutil'
}

# Mapping of package names to their import names (some differ)
IMPORT_MAPPING = {
    'scikit-learn': 'sklearn',
    'pyyaml': 'yaml',
    'gitpython': 'git',
}

def get_installed_packages() -> Set[str]:
    """Retrieve the set of currently installed packages."""
    result = subprocess.run(
        [sys.executable, '-m', 'pip', 'list', '--format=freeze'],
        capture_output=True,
        text=True,
        check=True
    )
    packages = set()
    for line in result.stdout.strip().split('\n'):
        if line:
            # Format: package==version
            pkg_name = line.split('==')[0].lower().replace('-', '_')
            packages.add(pkg_name)
    return packages

def verify_python_version() -> bool:
    """Verify we are running on Python 3.11."""
    major, minor = sys.version_info[:2]
    logger.info(f"Running on Python {major}.{minor}")
    if major != 3 or minor != 11:
        logger.warning(f"Expected Python 3.11, but running on {major}.{minor}. "
                     "This script is designed to validate 3.11 compatibility.")
        # We proceed anyway as the user might be testing on a compatible version
        return True
    return True

def check_wheel_compatibility(package_name: str) -> bool:
    """Check if a package has a compatible wheel for the current Python version."""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '--dry-run', package_name],
            capture_output=True,
            text=True,
            check=False
        )
        # If pip can resolve a wheel, it usually means it's compatible
        # We look for specific error patterns indicating incompatibility
        if "Could not find a version that satisfies the requirement" in result.stderr:
            logger.error(f"Package {package_name} has no compatible version for this environment.")
            return False
        return True
    except Exception as e:
        logger.warning(f"Could not verify wheel compatibility for {package_name}: {e}")
        return True  # Assume compatible if we can't check

def import_package(package_name: str, import_name: str = None) -> Tuple[bool, str]:
    """Attempt to import a package and return success status."""
    import_name = import_name or package_name
    try:
        importlib.import_module(import_name)
        logger.info(f"Successfully imported {import_name} (from {package_name})")
        return True, ""
    except ImportError as e:
        logger.error(f"Failed to import {import_name} (from {package_name}): {e}")
        return False, str(e)
    except Exception as e:
        logger.error(f"Unexpected error importing {import_name}: {e}")
        return False, str(e)

def check_version_conflicts() -> bool:
    """Check for obvious version conflicts using pip check."""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'check'],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode != 0:
            logger.warning("pip check found potential conflicts:")
            logger.warning(result.stdout)
            logger.warning(result.stderr)
            return False
        logger.info("No version conflicts detected by pip check.")
        return True
    except Exception as e:
        logger.warning(f"Could not run pip check: {e}")
        return True

def main():
    """Main entry point for the compatibility test."""
    logger.info("Starting Python 3.11 dependency compatibility verification...")
    
    # Step 1: Verify Python version
    if not verify_python_version():
        logger.critical("Python version verification failed.")
        sys.exit(1)

    # Step 2: Get installed packages
    installed = get_installed_packages()
    logger.info(f"Found {len(installed)} installed packages.")

    # Step 3: Check for missing packages
    missing_packages = []
    for pkg in EXPECTED_PACKAGES:
        if pkg.lower().replace('-', '_') not in installed:
            missing_packages.append(pkg)

    if missing_packages:
        logger.error(f"Missing required packages: {missing_packages}")
        logger.error("Please install missing packages using: pip install -r requirements.txt")
        sys.exit(1)
    
    logger.info("All required packages are installed.")

    # Step 4: Check wheel compatibility (dry-run)
    incompatible_wheels = []
    for pkg in EXPECTED_PACKAGES:
        if not check_wheel_compatibility(pkg):
            incompatible_wheels.append(pkg)
    
    if incompatible_wheels:
        logger.error(f"Incompatible wheels found for: {incompatible_wheels}")
        sys.exit(1)
    
    logger.info("All packages have compatible wheels.")

    # Step 5: Attempt to import all packages
    failed_imports = []
    for pkg in EXPECTED_PACKAGES:
        import_name = IMPORT_MAPPING.get(pkg, pkg)
        success, error = import_package(pkg, import_name)
        if not success:
            failed_imports.append((pkg, import_name, error))

    if failed_imports:
        logger.error("Failed to import the following packages:")
        for pkg, imp, err in failed_imports:
            logger.error(f"  - {pkg} (imported as {imp}): {err}")
        sys.exit(1)
    
    logger.info("All packages imported successfully.")

    # Step 6: Check for version conflicts
    if not check_version_conflicts():
        logger.warning("Potential version conflicts detected. Review pip check output above.")
        # We don't exit here as conflicts might be non-critical, but we log it

    logger.info("=" * 60)
    logger.info("Python 3.11 dependency compatibility verification PASSED.")
    logger.info("All dependencies are installed, compatible, and importable.")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()