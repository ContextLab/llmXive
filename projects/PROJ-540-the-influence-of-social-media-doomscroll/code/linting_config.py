"""
Linting and formatting configuration utilities.
Provides wrappers for flake8, black, and isort execution.
"""
import subprocess
import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def run_flake8() -> bool:
    """
    Run flake8 linting checks on the project.
    
    Returns:
        bool: True if checks pass, False otherwise.
    """
    logger.info("Running flake8 linting checks...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", "."],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            logger.info("flake8 checks passed.")
            return True
        else:
            logger.error("flake8 found issues:")
            logger.error(result.stdout)
            logger.error(result.stderr)
            return False
    except FileNotFoundError:
        logger.error("flake8 not found. Install with: pip install flake8")
        return False
    except Exception as e:
        logger.error(f"Error running flake8: {e}")
        return False

def run_black(check_only: bool = True) -> bool:
    """
    Run black formatting checks or formatting.
    
    Args:
        check_only: If True, only check formatting (dry-run). 
                    If False, apply formatting.
                    
    Returns:
        bool: True if checks pass or formatting applied successfully.
    """
    mode = "check" if check_only else "format"
    logger.info(f"Running black {mode}...")
    try:
        cmd = [sys.executable, "-m", "black", "."]
        if check_only:
            cmd.append("--check")
            cmd.append("--diff")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            logger.info("black formatting is correct.")
            return True
        else:
            if check_only:
                logger.error("black formatting issues found. Run 'black .' to fix.")
                logger.error(result.stdout)
            else:
                logger.info("black formatting applied.")
            return False
    except FileNotFoundError:
        logger.error("black not found. Install with: pip install black")
        return False
    except Exception as e:
        logger.error(f"Error running black: {e}")
        return False

def run_isort(check_only: bool = True) -> bool:
    """
    Run isort import sorting checks or fixing.
    
    Args:
        check_only: If True, only check sorting (dry-run).
                    If False, apply sorting.
                    
    Returns:
        bool: True if checks pass or sorting applied successfully.
    """
    mode = "check" if check_only else "fix"
    logger.info(f"Running isort {mode}...")
    try:
        cmd = [sys.executable, "-m", "isort", "."]
        if check_only:
            cmd.append("--check-only")
            cmd.append("--diff")
        else:
            cmd.append("--profile")
            cmd.append("black")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            logger.info("isort sorting is correct.")
            return True
        else:
            if check_only:
                logger.error("isort sorting issues found. Run 'isort .' to fix.")
                logger.error(result.stdout)
            else:
                logger.info("isort sorting applied.")
            return False
    except FileNotFoundError:
        logger.error("isort not found. Install with: pip install isort")
        return False
    except Exception as e:
        logger.error(f"Error running isort: {e}")
        return False

def run_all_checks() -> bool:
    """
    Run all linting and formatting checks (flake8, black, isort).
    
    Returns:
        bool: True if all checks pass, False otherwise.
    """
    logger.info("Running all linting and formatting checks...")
    results = [
        run_flake8(),
        run_black(check_only=True),
        run_isort(check_only=True)
    ]
    all_passed = all(results)
    if all_passed:
        logger.info("All checks passed.")
    else:
        logger.warning("Some checks failed.")
    return all_passed

def run_all_formatters() -> bool:
    """
    Run all formatters to fix code style (black, isort).
    
    Returns:
        bool: True if all formatters succeeded, False otherwise.
    """
    logger.info("Running all formatters...")
    results = [
        run_black(check_only=False),
        run_isort(check_only=False)
    ]
    all_success = all(results)
    if all_success:
        logger.info("All formatters applied successfully.")
    else:
        logger.warning("Some formatters failed.")
    return all_success

def main():
    """Main entry point for linting configuration script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    import argparse
    parser = argparse.ArgumentParser(description="Run linting and formatting tools.")
    parser.add_argument(
        "--check", 
        action="store_true", 
        help="Run only checks (do not modify files)"
    )
    parser.add_argument(
        "--fix", 
        action="store_true", 
        help="Run formatters to fix issues"
    )
    parser.add_argument(
        "--all", 
        action="store_true", 
        help="Run all checks and formatters"
    )
    
    args = parser.parse_args()
    
    if args.all:
        run_all_checks()
        run_all_formatters()
    elif args.fix:
        run_all_formatters()
    else:
        run_all_checks()

if __name__ == "__main__":
    main()