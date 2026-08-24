"""
Linting and formatting configuration utilities.

Provides functions to run flake8, black, and isort checks programmatically
or via CLI entry point.
"""
import subprocess
import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def run_flake8() -> bool:
    """
    Run flake8 linter on the codebase.
    
    Returns:
        True if linter passes, False otherwise.
    """
    logger.info("Running flake8...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", "."],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            logger.info("flake8 passed.")
            return True
        else:
            logger.error("flake8 failed:")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        logger.error(f"Error running flake8: {e}")
        return False

def run_black(check_only: bool = True) -> bool:
    """
    Run black formatter on the codebase.
    
    Args:
        check_only: If True, only check formatting (dry run).
                   If False, format files in place.
    
    Returns:
        True if formatting is correct (or applied), False otherwise.
    """
    mode = "--check" if check_only else ""
    logger.info(f"Running black {'(check)' if check_only else '(format)'}...")
    try:
        cmd = [sys.executable, "-m", "black", mode, "."]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            logger.info("black passed.")
            return True
        else:
            if check_only:
                logger.error("black formatting check failed. Run with --format to fix.")
            else:
                logger.info("black formatting applied.")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        logger.error(f"Error running black: {e}")
        return False

def run_isort(check_only: bool = True) -> bool:
    """
    Run isort import sorter on the codebase.
    
    Args:
        check_only: If True, only check sorting (dry run).
                   If False, sort imports in place.
    
    Returns:
        True if imports are correct (or sorted), False otherwise.
    """
    mode = "--check-only" if check_only else ""
    logger.info(f"Running isort {'(check)' if check_only else '(sort)'}...")
    try:
        cmd = [sys.executable, "-m", "isort", mode, "."]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            logger.info("isort passed.")
            return True
        else:
            if check_only:
                logger.error("isort sorting check failed. Run with --sort to fix.")
            else:
                logger.info("isort sorting applied.")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        logger.error(f"Error running isort: {e}")
        return False

def run_all_checks() -> bool:
    """
    Run all linting and formatting checks.
    
    Returns:
        True if all checks pass, False otherwise.
    """
    logger.info("Running all linting checks...")
    results = [
        run_flake8(),
        run_black(check_only=True),
        run_isort(check_only=True)
    ]
    return all(results)

def run_all_formatters() -> bool:
    """
    Run all formatters to fix issues.
    
    Returns:
        True if all formatters succeeded, False otherwise.
    """
    logger.info("Running all formatters...")
    results = [
        run_black(check_only=False),
        run_isort(check_only=False)
    ]
    return all(results)

def main():
    """CLI entry point for linting tools."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run linting and formatting tools.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run all checks without modifying files."
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Run formatters to fix issues."
    )
    parser.add_argument(
        "--flake8",
        action="store_true",
        help="Run only flake8."
    )
    parser.add_argument(
        "--black",
        action="store_true",
        help="Run only black."
    )
    parser.add_argument(
        "--isort",
        action="store_true",
        help="Run only isort."
    )
    
    args = parser.parse_args()
    
    # Default behavior: run all checks
    if not (args.check or args.fix or args.flake8 or args.black or args.isort):
        args.check = True
    
    success = True
    
    if args.flake8:
        success &= run_flake8()
    if args.black:
        success &= run_black(check_only=not args.fix)
    if args.isort:
        success &= run_isort(check_only=not args.fix)
    if args.check:
        success &= run_all_checks()
    if args.fix:
        success &= run_all_formatters()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()