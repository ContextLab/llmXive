"""
Linting and formatting configuration utilities.
Provides functions to run flake8, black, and isort checks/formatters.
"""
import subprocess
import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def run_flake8(project_root: Optional[Path] = None) -> bool:
    """
    Run flake8 linting checks on the project.
    
    Args:
        project_root: Root directory of the project. Defaults to current working directory.
        
    Returns:
        True if checks pass (exit code 0), False otherwise.
    """
    if project_root is None:
        project_root = Path.cwd()
        
    logger.info("Running flake8 linting checks...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", str(project_root)],
            cwd=project_root,
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error running flake8: {e}")
        return False

def run_black(project_root: Optional[Path] = None, check_only: bool = False) -> bool:
    """
    Run black code formatter on the project.
    
    Args:
        project_root: Root directory of the project. Defaults to current working directory.
        check_only: If True, only check formatting without modifying files.
        
    Returns:
        True if formatting is correct (or fixed), False if errors occurred.
    """
    if project_root is None:
        project_root = Path.cwd()
        
    logger.info("Running black code formatter..." if not check_only else "Checking black formatting...")
    cmd = [sys.executable, "-m", "black"]
    if check_only:
        cmd.append("--check")
        cmd.append("--diff")
        
    cmd.append(str(project_root))
    
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error running black: {e}")
        return False

def run_isort(project_root: Optional[Path] = None, check_only: bool = False) -> bool:
    """
    Run isort import sorter on the project.
    
    Args:
        project_root: Root directory of the project. Defaults to current working directory.
        check_only: If True, only check sorting without modifying files.
        
    Returns:
        True if imports are sorted correctly (or fixed), False if errors occurred.
    """
    if project_root is None:
        project_root = Path.cwd()
        
    logger.info("Running isort import sorter..." if not check_only else "Checking isort formatting...")
    cmd = [sys.executable, "-m", "isort"]
    if check_only:
        cmd.append("--check-only")
        cmd.append("--diff")
        
    cmd.append(str(project_root))
    
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error running isort: {e}")
        return False

def run_all_checks(project_root: Optional[Path] = None) -> bool:
    """
    Run all linting checks (flake8, black check, isort check).
    
    Args:
        project_root: Root directory of the project. Defaults to current working directory.
        
    Returns:
        True if all checks pass, False otherwise.
    """
    if project_root is None:
        project_root = Path.cwd()
        
    logger.info("Running all linting checks...")
    
    checks = [
        ("flake8", run_flake8),
        ("black", lambda: run_black(project_root, check_only=True)),
        ("isort", lambda: run_isort(project_root, check_only=True)),
    ]
    
    all_passed = True
    for name, check_func in checks:
        logger.info(f"Checking {name}...")
        if not check_func():
            logger.error(f"{name} check failed")
            all_passed = False
        else:
            logger.info(f"{name} check passed")
            
    if all_passed:
        logger.info("All linting checks passed!")
    else:
        logger.error("Some linting checks failed. Please fix the issues.")
        
    return all_passed

def run_all_formatters(project_root: Optional[Path] = None) -> bool:
    """
    Run all formatters (black, isort) to fix formatting issues.
    
    Args:
        project_root: Root directory of the project. Defaults to current working directory.
        
    Returns:
        True if all formatters succeeded, False otherwise.
    """
    if project_root is None:
        project_root = Path.cwd()
        
    logger.info("Running all formatters...")
    
    formatters = [
        ("black", lambda: run_black(project_root, check_only=False)),
        ("isort", lambda: run_isort(project_root, check_only=False)),
    ]
    
    all_succeeded = True
    for name, formatter_func in formatters:
        logger.info(f"Running {name}...")
        if not formatter_func():
            logger.error(f"{name} failed")
            all_succeeded = False
        else:
            logger.info(f"{name} completed successfully")
            
    if all_succeeded:
        logger.info("All formatters completed successfully!")
    else:
        logger.error("Some formatters failed.")
        
    return all_succeeded

def main():
    """Main entry point for running linting checks and formatters."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run linting and formatting tools")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only run checks without fixing issues"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Run formatters to fix issues"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run both checks and formatters"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Project root directory (default: current directory)"
    )
    
    args = parser.parse_args()
    
    if not (args.check or args.fix or args.all):
        # Default to checks only
        args.check = True
        
    project_root = args.project_root or Path.cwd()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if args.check or args.all:
        run_all_checks(project_root)
        
    if args.fix or args.all:
        run_all_formatters(project_root)

if __name__ == "__main__":
    main()
