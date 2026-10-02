"""
Environment verification script for PROJ-312.

This script verifies that all required dependencies are installed
and that all critical imports from the project's codebase succeed.
"""
import subprocess
import sys
import logging
from pathlib import Path

def setup_logging():
    """Configure logging for the verification script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def verify_imports():
    """
    Verify that all critical imports from the project's codebase succeed.
    
    Returns:
        bool: True if all imports succeed, False otherwise.
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # List of critical modules to import
    # These are the core modules that the pipeline depends on
    critical_modules = [
        'code.utils',
        'code.fetch_data',
        'code.analyze',
        'code.visualize',
        'code.report',
        'code.validate_spot_check',
        'code.data_quality',
        'code.logging_config',
        'code.save_raw_data',
        'code.save_processed_data',
        'code.save_statistical_results',
        'code.save_spot_check_results',
        'code.update_state',
        'code.verify_schemas',
        'code.verify_boxplot',
    ]
    
    failed_imports = []
    
    logger.info("Verifying critical module imports...")
    
    for module_name in critical_modules:
        try:
            __import__(module_name)
            logger.info(f"  ✓ Successfully imported {module_name}")
        except ImportError as e:
            logger.error(f"  ✗ Failed to import {module_name}: {e}")
            failed_imports.append((module_name, str(e)))
        except Exception as e:
            logger.error(f"  ✗ Error importing {module_name}: {e}")
            failed_imports.append((module_name, str(e)))
    
    if failed_imports:
        logger.error(f"\n❌ Verification FAILED: {len(failed_imports)} import(s) failed")
        for module, error in failed_imports:
            logger.error(f"  - {module}: {error}")
        return False
    
    logger.info("\n✅ All critical imports successful!")
    return True

def verify_dependencies():
    """
    Verify that all required dependencies from requirements.txt are installed.
    
    Returns:
        bool: True if all dependencies are installed, False otherwise.
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Read requirements.txt
    requirements_path = Path("projects/PROJ-312-evaluating-the-impact-of-code-generation/requirements.txt")
    
    if not requirements_path.exists():
        logger.error(f"Requirements file not found: {requirements_path}")
        return False
    
    with open(requirements_path, 'r') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    logger.info(f"Checking {len(requirements)} dependencies from requirements.txt...")
    
    missing_deps = []
    
    for req in requirements:
        # Extract package name (handle ==, >=, etc.)
        package_name = req.split('==')[0].split('>=')[0].split('<=')[0].split('[')[0]
        
        try:
            # Try to import the package
            __import__(package_name)
            logger.info(f"  ✓ {package_name} is installed")
        except ImportError:
            logger.warning(f"  ✗ {package_name} is NOT installed")
            missing_deps.append(package_name)
    
    if missing_deps:
        logger.error(f"\n❌ Missing dependencies: {', '.join(missing_deps)}")
        logger.info("Run: pip install -r projects/PROJ-312-evaluating-the-impact-of-code-generation/requirements.txt")
        return False
    
    logger.info("\n✅ All dependencies installed!")
    return True

def main():
    """Main entry point for environment verification."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("Environment Verification for PROJ-312")
    logger.info("=" * 60)
    
    # Verify dependencies
    deps_ok = verify_dependencies()
    
    # Verify imports
    imports_ok = verify_imports()
    
    # Final status
    logger.info("=" * 60)
    if deps_ok and imports_ok:
        logger.info("✅ Environment verification PASSED")
        logger.info("=" * 60)
        return 0
    else:
        logger.error("❌ Environment verification FAILED")
        logger.info("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())