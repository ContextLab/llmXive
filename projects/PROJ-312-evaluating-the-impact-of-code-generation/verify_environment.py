"""
Verify Environment Task (T002b)

This script verifies that all dependencies listed in requirements.txt
are correctly installed and that their primary import names succeed.
"""
import subprocess
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    project_root = Path(__file__).parent
    requirements_path = project_root / "requirements.txt"

    if not requirements_path.exists():
        logger.error(f"requirements.txt not found at {requirements_path}")
        sys.exit(1)

    logger.info(f"Verifying environment using: {requirements_path}")

    # 1. Install/Upgrade dependencies
    logger.info("Installing dependencies from requirements.txt...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)],
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            logger.debug(result.stdout)
        if result.stderr:
            logger.debug(result.stderr)
        logger.info("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e.stderr}")
        sys.exit(1)

    # 2. Verify imports
    # Mapping of package names to their primary import names as per requirements
    # requests -> requests
    # pandas -> pandas
    # scipy -> scipy
    # matplotlib -> matplotlib
    # pyyaml -> yaml
    # tqdm -> tqdm
    # statsmodels -> statsmodels
    imports_to_check = [
        "requests",
        "pandas",
        "scipy",
        "matplotlib",
        "yaml",
        "tqdm",
        "statsmodels"
    ]

    failed_imports = []
    for module_name in imports_to_check:
        try:
            __import__(module_name)
            logger.info(f"  [OK] {module_name} imported successfully.")
        except ImportError as e:
            logger.error(f"  [FAIL] Failed to import {module_name}: {e}")
            failed_imports.append(module_name)

    if failed_imports:
        logger.error(f"Environment verification failed. Missing modules: {failed_imports}")
        sys.exit(1)

    logger.info("Environment verification complete. All dependencies installed and importable.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
