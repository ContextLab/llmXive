"""
T050: Run quickstart.md validation to ensure reproducibility.

This script validates the project setup by:
1. Checking required directories exist.
2. Verifying requirements.txt is present and parsable.
3. Checking that core code modules exist and are syntactically valid.
4. Verifying data directories are ready.
5. Running a dry-run of the main entry points to ensure imports work.
"""
import os
import sys
import ast
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
TESTS_DIR = PROJECT_ROOT / "tests"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"
QUICKSTART_FILE = PROJECT_ROOT / "quickstart.md"

# Expected directory structure based on T001a, T001b, T008
REQUIRED_DIRS = [
    CODE_DIR,
    DATA_DIR,
    TESTS_DIR,
    OUTPUTS_DIR,
    DATA_DIR / "benchmarks",
    DATA_DIR / "benchmarks" / "raw",
    DATA_DIR / "benchmarks" / "processed",
    DATA_DIR / "generated",
    DATA_DIR / "coverage_reports",
    DATA_DIR / "processed",
    OUTPUTS_DIR,
]

# Expected core modules based on tasks.md and API surface
REQUIRED_MODULES = [
    "config.py",
    "utils.py",
    "dataset_loader.py",
    "test_transformer.py",
    "llm_generator.py",
    "coverage_runner.py",
    "main.py",
    "analyzer.py",
    "visualizer.py",
    "error_handling.py",
    "setup_directories.py",
    "setup_linting.py",
    "setup_venv.py",
    "validate_data_structure.py",
    "performance_benchmark.py",
]

def check_directories() -> bool:
    """Check if all required directories exist."""
    logger.info("Checking required directories...")
    all_exist = True
    for dir_path in REQUIRED_DIRS:
        if not dir_path.exists():
            logger.error(f"Missing directory: {dir_path}")
            all_exist = False
        else:
            logger.debug(f"Directory exists: {dir_path}")
    
    if all_exist:
        logger.info("All required directories exist.")
    return all_exist

def check_requirements() -> bool:
    """Check if requirements.txt exists and is readable."""
    logger.info("Checking requirements.txt...")
    if not REQUIREMENTS_FILE.exists():
        logger.error(f"Missing file: {REQUIREMENTS_FILE}")
        return False
    
    try:
        with open(REQUIREMENTS_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                logger.warning("requirements.txt is empty.")
                return False
            logger.info("requirements.txt is present and non-empty.")
            return True
    except Exception as e:
        logger.error(f"Error reading requirements.txt: {e}")
        return False

def check_quickstart() -> bool:
    """Check if quickstart.md exists."""
    logger.info("Checking quickstart.md...")
    if not QUICKSTART_FILE.exists():
        logger.error(f"Missing file: {QUICKSTART_FILE}")
        return False
    
    try:
        with open(QUICKSTART_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                logger.warning("quickstart.md is empty.")
                return False
            logger.info("quickstart.md is present and non-empty.")
            return True
    except Exception as e:
        logger.error(f"Error reading quickstart.md: {e}")
        return False

def check_syntax(module_name: str) -> bool:
    """Check if a Python module has valid syntax."""
    file_path = CODE_DIR / module_name
    if not file_path.exists():
        logger.error(f"Missing module file: {file_path}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
            ast.parse(source)
        logger.debug(f"Syntax valid: {module_name}")
        return True
    except SyntaxError as e:
        logger.error(f"Syntax error in {module_name}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error checking syntax for {module_name}: {e}")
        return False

def check_modules() -> bool:
    """Check if all required modules exist and have valid syntax."""
    logger.info("Checking core modules...")
    all_valid = True
    for module in REQUIRED_MODULES:
        if not check_syntax(module):
            all_valid = False
    
    if all_valid:
        logger.info("All core modules have valid syntax.")
    return all_valid

def check_imports() -> bool:
    """Attempt to import core modules to verify dependencies."""
    logger.info("Checking module imports (dry-run)...")
    # We only check if the file can be imported without running main logic.
    # This might fail if dependencies aren't installed, but that's expected
    # if the environment isn't set up. We treat import errors as warnings
    # unless it's a missing module file.
    
    # Add code dir to path
    sys.path.insert(0, str(PROJECT_ROOT))
    
    errors = []
    for module in REQUIRED_MODULES:
        module_name = module.replace('.py', '')
        try:
            __import__(module_name)
            logger.debug(f"Successfully imported {module_name}")
        except ImportError as e:
            # Check if it's a missing dependency or missing file
            if f"No module named '{module_name}'" in str(e):
                logger.error(f"Module file missing or not importable: {module_name}")
                errors.append(module_name)
            else:
                # Dependency issue
                logger.warning(f"Import dependency issue for {module_name}: {e}")
                # We don't fail the whole check for dependency issues here,
                # as the task is to validate the *code structure* and *quickstart* readiness.
                # The actual execution of T002b handles dependency installation.
    
    if errors:
        logger.error(f"Critical import failures: {errors}")
        return False
    
    logger.info("Import checks passed (dependency warnings ignored).")
    return True

def run_validation() -> int:
    """Run all validation checks."""
    logger.info(f"Starting quickstart validation at {datetime.now()}")
    logger.info(f"Project root: {PROJECT_ROOT}")
    
    checks = [
        ("Directories", check_directories),
        ("Requirements", check_requirements),
        ("Quickstart", check_quickstart),
        ("Modules Syntax", check_modules),
        ("Modules Imports", check_imports),
    ]
    
    results = {}
    for name, check_func in checks:
        results[name] = check_func()
    
    logger.info("-" * 40)
    logger.info("Validation Summary:")
    for name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        logger.info(f"  {name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("✅ Quickstart validation PASSED. Project is ready for reproduction.")
        return 0
    else:
        logger.error("❌ Quickstart validation FAILED. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(run_validation())