import subprocess
import sys
import logging
from pathlib import Path
import pkg_resources

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_package_installed(package_name: str) -> bool:
    """Check if a package is installed."""
    try:
        pkg_resources.get_distribution(package_name)
        return True
    except pkg_resources.DistributionNotFound:
        return False

def get_package_version(package_name: str) -> str:
    """Get the version of an installed package."""
    try:
        return pkg_resources.get_distribution(package_name).version
    except pkg_resources.DistributionNotFound:
        return "Not installed"

def validate_dependencies() -> bool:
    """Validate that all required dependencies are installed."""
    required_packages = [
        'pandas',
        'numpy',
        'scikit-learn',
        'statsmodels',
        'scipy',
        'matplotlib',
        'seaborn',
        'pyyaml',
        'requests',
        'rasterio',
        'geopandas',
        'pyproj'
    ]

    missing_packages = []
    for package in required_packages:
        if not check_package_installed(package):
            missing_packages.append(package)

    if missing_packages:
        logger.warning(f"Missing packages: {', '.join(missing_packages)}")
        return False

    logger.info("All required dependencies are installed.")
    return True

def install_dependencies() -> None:
    """Install missing dependencies."""
    required_packages = [
        'pandas',
        'numpy',
        'scikit-learn',
        'statsmodels',
        'scipy',
        'matplotlib',
        'seaborn',
        'pyyaml',
        'requests',
        'rasterio',
        'geopandas',
        'pyproj'
    ]

    missing_packages = []
    for package in required_packages:
        if not check_package_installed(package):
            missing_packages.append(package)

    if not missing_packages:
        logger.info("All dependencies are already installed.")
        return

    logger.info(f"Installing missing packages: {', '.join(missing_packages)}")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
        logger.info("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        sys.exit(1)

def main():
    """Main entry point for dependency setup."""
    logger.info("Starting dependency validation and installation...")
    
    if not validate_dependencies():
        logger.info("Some dependencies are missing. Attempting installation...")
        install_dependencies()
    else:
        logger.info("All dependencies are satisfied.")

    logger.info("Dependency setup complete.")

if __name__ == "__main__":
    main()