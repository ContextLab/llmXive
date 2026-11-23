"""
Linting and formatting configuration and execution utilities.

This module provides functions to ensure ruff and black are configured,
and to run linting and formatting commands programmatically.
"""
import os
import subprocess
import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def ensure_ruff_config() -> bool:
    """
    Ensure .ruff.toml or ruff config in pyproject.toml exists.
    Returns True if config is valid, False otherwise.
    """
    root = Path.cwd()
    ruff_toml = root / ".ruff.toml"
    pyproject = root / "pyproject.toml"

    if ruff_toml.exists():
        logger.info("Found .ruff.toml configuration")
        return True
    
    if pyproject.exists():
        content = pyproject.read_text()
        if "[tool.ruff]" in content:
            logger.info("Found ruff configuration in pyproject.toml")
            return True
    
    logger.warning("No ruff configuration found. Using defaults.")
    return True

def ensure_black_config() -> bool:
    """
    Ensure black configuration exists in pyproject.toml or setup.cfg.
    Returns True if config is valid, False otherwise.
    """
    root = Path.cwd()
    pyproject = root / "pyproject.toml"
    setup_cfg = root / "setup.cfg"
    black_cfg = root / "black.toml"

    if black_cfg.exists():
        logger.info("Found black.toml configuration")
        return True
    
    if pyproject.exists():
        content = pyproject.read_text()
        if "[tool.black]" in content:
            logger.info("Found black configuration in pyproject.toml")
            return True
    
    if setup_cfg.exists():
        content = setup_cfg.read_text()
        if "[black]" in content:
            logger.info("Found black configuration in setup.cfg")
            return True
    
    logger.warning("No black configuration found. Using defaults.")
    return True

def run_isort() -> Tuple[int, str, str]:
    """
    Run isort to sort imports.
    Returns (exit_code, stdout, stderr).
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "isort", "."],
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        logger.error("isort not found. Install with: pip install isort")
        return 1, "", "isort not found"

def run_lint() -> Tuple[int, str, str]:
    """
    Run ruff linter.
    Returns (exit_code, stdout, stderr).
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "."],
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        logger.error("ruff not found. Install with: pip install ruff")
        return 1, "", "ruff not found"

def run_format() -> Tuple[int, str, str]:
    """
    Run black formatter.
    Returns (exit_code, stdout, stderr).
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "."],
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        logger.error("black not found. Install with: pip install black")
        return 1, "", "black not found"

def main() -> int:
    """
    Main entry point for linting and formatting CLI.
    Usage: python -m code.lint_config [check|fix|format|lint]
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    if len(sys.argv) < 2:
        print("Usage: python -m code.lint_config [check|fix|format|lint]")
        print("  check: Run linters without fixing")
        print("  fix: Run linters and formatters to fix issues")
        print("  format: Run black only")
        print("  lint: Run ruff only")
        return 1

    command = sys.argv[1].lower()

    # Ensure configurations exist
    ensure_ruff_config()
    ensure_black_config()

    if command == "check":
        logger.info("Running lint check...")
        code, out, err = run_lint()
        if out:
            print(out)
        if err:
            print(err, file=sys.stderr)
        if code != 0:
            logger.error("Linting found issues")
            return code
        logger.info("Linting passed")
        return 0

    elif command == "fix":
        logger.info("Running formatter...")
        code, out, err = run_format()
        if out:
            print(out)
        if err:
            print(err, file=sys.stderr)
        
        logger.info("Running linter with auto-fix...")
        code, out, err = run_lint()
        if out:
            print(out)
        if err:
            print(err, file=sys.stderr)
        return code

    elif command == "format":
        logger.info("Running black formatter...")
        code, out, err = run_format()
        if out:
            print(out)
        if err:
            print(err, file=sys.stderr)
        return code

    elif command == "lint":
        logger.info("Running ruff linter...")
        code, out, err = run_lint()
        if out:
            print(out)
        if err:
            print(err, file=sys.stderr)
        return code

    else:
        print(f"Unknown command: {command}")
        return 1

if __name__ == "__main__":
    sys.exit(main())