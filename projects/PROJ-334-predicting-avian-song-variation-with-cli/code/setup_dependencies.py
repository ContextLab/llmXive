"""
Setup script to validate and install project dependencies.
This script ensures that all required packages listed in requirements.txt
are installed and compatible with the current Python environment.
"""
import subprocess
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_package_installed(package_name: str) -> bool:
    """Check if a package is installed."""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False

def get_package_version(package_name: str) -> str:
    """Get the installed version of a package."""
    try:
        import importlib.metadata
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return "Not installed"

def validate_dependencies(requirements_path: Path) -> bool:
    """
    Validate that all dependencies in requirements.txt are installed.
    
    Args:
        requirements_path: Path to requirements.txt file
        
    Returns:
        True if all dependencies are satisfied, False otherwise
    """
    if not requirements_path.exists():
        logger.error(f"Requirements file not found: {requirements_path}")
        return False

    missing_packages = []
    
    with open(requirements_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Extract package name (remove version specifiers)
            package_name = line.split('>=')[0].split('==')[0].split('<=')[0].split('>=')[0].split('~=')[0]
            
            if not check_package_installed(package_name):
                missing_packages.append(package_name)
                logger.warning(f"Missing package: {package_name}")
            else:
                version = get_package_version(package_name)
                logger.info(f"Installed: {package_name} (v{version})")

    if missing_packages:
        logger.error(f"Missing packages: {', '.join(missing_packages)}")
        logger.info("Run 'pip install -r requirements.txt' to install missing dependencies")
        return False

    logger.info("All dependencies are satisfied!")
    return True

def install_dependencies(requirements_path: Path) -> bool:
    """
    Install all dependencies from requirements.txt.
    
    Args:
        requirements_path: Path to requirements.txt file
        
    Returns:
        True if installation was successful, False otherwise
    """
    if not requirements_path.exists():
        logger.error(f"Requirements file not found: {requirements_path}")
        return False

    logger.info(f"Installing dependencies from {requirements_path}...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_path)
        ])
        logger.info("Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        return False

def main():
    """Main entry point for dependency setup."""
    # Determine project root
    project_root = Path(__file__).parent.parent
    requirements_path = project_root / "requirements.txt"

    logger.info(f"Project root: {project_root}")
    logger.info(f"Requirements file: {requirements_path}")

    # First, try to install dependencies
    if not requirements_path.exists():
        logger.error("requirements.txt not found. Please create it with required dependencies.")
        sys.exit(1)

    # Install dependencies
    if not install_dependencies(requirements_path):
        sys.exit(1)

    # Validate installation
    if not validate_dependencies(requirements_path):
        sys.exit(1)

    logger.info("Dependency setup completed successfully!")

if __name__ == "__main__":
    main()