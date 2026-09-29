"""
T002b: Verify environment by installing requirements and testing imports.
This script ensures all dependencies are correctly installed and importable.
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

def verify_imports():
    """Verify that all required packages can be imported."""
    required_packages = [
        'requests',
        'pandas',
        'scipy',
        'matplotlib',
        'yaml',  # from pyyaml
        'tqdm',
        'statsmodels'
    ]

    failed_imports = []

    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"Successfully imported: {package}")
        except ImportError as e:
            logger.error(f"Failed to import {package}: {e}")
            failed_imports.append(package)

    return failed_imports

def main():
    project_root = Path(__file__).resolve().parent.parent
    requirements_path = project_root / "projects" / "PROJ-312-evaluating-the-impact-of-code-generation" / "requirements.txt"

    if not requirements_path.exists():
        logger.error(f"Requirements file not found: {requirements_path}")
        sys.exit(1)

    logger.info(f"Installing requirements from: {requirements_path}")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("Requirements installed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install requirements: {e.stderr}")
        sys.exit(1)

    logger.info("Verifying imports...")
    failed = verify_imports()

    if failed:
        logger.error(f"Environment verification failed. Missing packages: {failed}")
        sys.exit(1)

    logger.info("Environment verification successful. All packages installed and importable.")
    sys.exit(0)

if __name__ == "__main__":
    main()
