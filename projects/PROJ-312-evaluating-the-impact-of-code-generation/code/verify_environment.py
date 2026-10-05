import subprocess
import sys
import logging
from pathlib import Path

def setup_logging():
    """Configure logging for the environment verification script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def verify_dependencies():
    """
    Verify that all dependencies listed in requirements.txt are installed.
    Reads the requirements file and attempts to import each package.
    """
    logger = logging.getLogger(__name__)
    project_root = Path(__file__).resolve().parent.parent
    requirements_path = project_root / "requirements.txt"

    if not requirements_path.exists():
        logger.error(f"Requirements file not found at: {requirements_path}")
        return False

    logger.info(f"Verifying dependencies from: {requirements_path}")
    
    try:
        with open(requirements_path, 'r') as f:
            lines = f.readlines()
    except IOError as e:
        logger.error(f"Failed to read requirements file: {e}")
        return False

    packages = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            # Handle package names with version specifiers
            pkg_name = line.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0].split('!=')[0].split('>')[0].split('<')[0]
            pkg_name = pkg_name.strip()
            if pkg_name:
                packages.append(pkg_name)

    logger.info(f"Found {len(packages)} packages to verify: {packages}")

    missing = []
    for pkg in packages:
        try:
            # Attempt to import the package
            __import__(pkg)
            logger.info(f"✓ Successfully imported: {pkg}")
        except ImportError:
            # Some packages might have different import names than pip names
            # e.g., 'scikit-learn' imports as 'sklearn'
            # For this specific project, we assume standard names or handle common cases
            import_names = {
                'scikit-learn': 'sklearn',
                'pyyaml': 'yaml',
                'pillow': 'PIL',
                'beautifulsoup4': 'bs4',
                'python-dateutil': 'dateutil'
            }
            
            import_name = import_names.get(pkg, pkg)
            try:
                __import__(import_name)
                logger.info(f"✓ Successfully imported (as {import_name}): {pkg}")
            except ImportError:
                logger.error(f"✗ Failed to import: {pkg} (tried {import_name})")
                missing.append(pkg)

    if missing:
        logger.error(f"Missing dependencies: {missing}")
        logger.error("Please run: pip install -r requirements.txt")
        return False

    logger.info("All dependencies verified successfully.")
    return True

def verify_imports():
    """
    Verify that all local modules in the code/ directory can be imported.
    This ensures the project structure is correct and dependencies between modules work.
    """
    logger = logging.getLogger(__name__)
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"

    if not code_dir.exists():
        logger.error(f"Code directory not found at: {code_dir}")
        return False

    logger.info(f"Verifying local imports from: {code_dir}")

    # Add the project root to sys.path to allow relative imports
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    failed_imports = []
    
    # Get all Python files in the code directory
    python_files = list(code_dir.glob("*.py"))
    
    for py_file in python_files:
        module_name = py_file.stem
        if module_name == '__init__':
            continue
        
        try:
            # Attempt to import the module
            __import__(f"code.{module_name}")
            logger.info(f"✓ Successfully imported module: code.{module_name}")
        except Exception as e:
            logger.error(f"✗ Failed to import module code.{module_name}: {e}")
            failed_imports.append((module_name, str(e)))

    if failed_imports:
        logger.error(f"Failed to import {len(failed_imports)} modules:")
        for module, error in failed_imports:
            logger.error(f"  - {module}: {error}")
        return False

    logger.info("All local modules verified successfully.")
    return True

def main():
    """Main entry point for environment verification."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting environment verification for PROJ-312...")
    
    deps_ok = verify_dependencies()
    imports_ok = verify_imports()
    
    if deps_ok and imports_ok:
        logger.info("Environment verification PASSED.")
        return 0
    else:
        logger.error("Environment verification FAILED.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
