import subprocess
import sys
import logging
from pathlib import Path
import pkg_resources

from utils import setup_logging

logger = None

def check_package_installed(package_name: str) -> bool:
    try:
        pkg_resources.require(package_name)
        return True
    except pkg_resources.DistributionNotFound:
        return False

def get_package_version(package_name: str) -> str:
    try:
        return pkg_resources.get_distribution(package_name).version
    except pkg_resources.DistributionNotFound:
        return "Not installed"

def validate_dependencies(requirements_path: Path) -> bool:
    """Validate that all dependencies in requirements.txt are installed."""
    if not requirements_path.exists():
        logging.error(f"Requirements file not found: {requirements_path}")
        return False

    all_installed = True
    with open(requirements_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # Extract package name without version specifiers
            package_name = line.split('>=')[0].split('<=')[0].split('==')[0].split('~=')[0].split('!=')[0].split('>')[0].split('<')[0].strip()
            if not check_package_installed(package_name):
                logging.warning(f"Missing package: {package_name}")
                all_installed = False
            else:
                logging.info(f"Found package: {package_name} v{get_package_version(package_name)}")
    
    return all_installed

def install_dependencies(requirements_path: Path) -> bool:
    """Install dependencies from requirements.txt."""
    if not requirements_path.exists():
        logging.error(f"Requirements file not found: {requirements_path}")
        return False

    logging.info(f"Installing dependencies from {requirements_path}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(requirements_path)])
        logging.info("Dependencies installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to install dependencies: {e}")
        return False

def main():
    global logger
    logger = setup_logging("setup_dependencies", "data/logs/setup_dependencies.log")
    
    project_root = Path(__file__).resolve().parent.parent
    requirements_path = project_root / "requirements.txt"

    if not requirements_path.exists():
        logger.error(f"Requirements file not found at {requirements_path}")
        sys.exit(1)

    logger.info("Validating dependencies...")
    if validate_dependencies(requirements_path):
        logger.info("All dependencies are satisfied.")
    else:
        logger.warning("Some dependencies are missing. Attempting installation...")
        if install_dependencies(requirements_path):
            logger.info("Dependencies installed successfully.")
        else:
            logger.error("Failed to install dependencies. Exiting.")
            sys.exit(1)

    logger.info("Dependency setup complete.")

if __name__ == "__main__":
    main()