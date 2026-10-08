"""
Environment verification script for PROJ-312.
Verifies that all dependencies in requirements.txt are installed and importable.
"""
import subprocess
import sys
import logging
from pathlib import Path

# Configure logging
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/pipeline.log', mode='a')
        ]
    )

def verify_dependencies(requirements_path: Path) -> bool:
    """
    Verify that dependencies listed in requirements.txt are installed.
    Returns True if all are installed, False otherwise.
    """
    if not requirements_path.exists():
        logging.error(f"Requirements file not found: {requirements_path}")
        return False

    logging.info(f"Checking dependencies from: {requirements_path}")
    
    try:
        # Read requirements
        with open(requirements_path, 'r') as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        if not requirements:
            logging.warning("No dependencies found in requirements.txt")
            return True

        # Check each requirement
        missing = []
        for req in requirements:
            # Extract package name (handle version specifiers)
            pkg_name = req.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0].split('!=')[0].split('<')[0].split('>')[0].strip()
            
            try:
                # Use pip show to check if installed
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'show', pkg_name],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode != 0:
                    missing.append(pkg_name)
                    logging.warning(f"Package not installed: {pkg_name}")
                else:
                    logging.info(f"Package installed: {pkg_name}")
            except subprocess.TimeoutExpired:
                missing.append(pkg_name)
                logging.warning(f"Timeout checking package: {pkg_name}")
            except Exception as e:
                missing.append(pkg_name)
                logging.warning(f"Error checking package {pkg_name}: {e}")

        if missing:
            logging.error(f"Missing dependencies: {', '.join(missing)}")
            logging.error("Run: pip install -r requirements.txt")
            return False

        logging.info("All dependencies installed successfully.")
        return True

    except Exception as e:
        logging.error(f"Error verifying dependencies: {e}")
        return False

def verify_imports() -> bool:
    """
    Verify that all required packages can be imported.
    Returns True if all imports succeed, False otherwise.
    """
    required_imports = [
        'requests',
        'pandas',
        'scipy',
        'matplotlib',
        'yaml',  # pyyaml
        'tqdm',
        'statsmodels'
    ]

    failed_imports = []
    
    for module in required_imports:
        try:
            __import__(module)
            logging.info(f"Successfully imported: {module}")
        except ImportError as e:
            failed_imports.append(module)
            logging.error(f"Failed to import {module}: {e}")

    if failed_imports:
        logging.error(f"Failed imports: {', '.join(failed_imports)}")
        return False

    logging.info("All imports successful.")
    return True

def main():
    """Main entry point for environment verification."""
    setup_logging()
    logging.info("Starting environment verification for PROJ-312")

    # Determine project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    requirements_path = project_root / 'requirements.txt'

    # Verify dependencies are installed
    deps_ok = verify_dependencies(requirements_path)
    
    if not deps_ok:
        logging.error("Dependency verification failed. Please install missing packages.")
        sys.exit(1)

    # Verify imports work
    imports_ok = verify_imports()
    
    if not imports_ok:
        logging.error("Import verification failed. Some packages may be installed but not importable.")
        sys.exit(1)

    logging.info("Environment verification completed successfully.")
    sys.exit(0)

if __name__ == '__main__':
    main()
