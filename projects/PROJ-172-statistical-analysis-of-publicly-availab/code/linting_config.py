"""
Configuration and execution helpers for linting (ruff) and formatting (black).

This module provides a programmatic interface to run checks and fixes
defined in pyproject.toml.
"""
import subprocess
import sys
import os
from pathlib import Path
from utils.logging import get_logger, log_info, log_error

logger = get_logger(__name__)

def get_project_root() -> Path:
    """Return the project root directory."""
    current = Path(__file__).resolve()
    # Traverse up until we find pyproject.toml or reach root
    for parent in [current] + list(current.parents):
        if (parent / "pyproject.toml").exists():
            return parent
    return current.parent

def run_ruff_check() -> int:
    """Run ruff check on the project.
    
    Returns:
        0 if check passes, non-zero otherwise.
    """
    project_root = get_project_root()
    cmd = [
        sys.executable, "-m", "ruff", "check", 
        str(project_root),
        "--config", str(project_root / "pyproject.toml")
    ]
    
    log_info(f"Running ruff check: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
        if result.returncode != 0:
            log_error("Ruff check failed:")
            logger.error(result.stdout)
            logger.error(result.stderr)
        else:
            log_info("Ruff check passed.")
        return result.returncode
    except Exception as e:
        log_error(f"Failed to run ruff check: {e}")
        return 1

def run_ruff_fix() -> int:
    """Run ruff check with automatic fixes.
    
    Returns:
        0 if successful, non-zero otherwise.
    """
    project_root = get_project_root()
    cmd = [
        sys.executable, "-m", "ruff", "check", 
        str(project_root),
        "--config", str(project_root / "pyproject.toml"),
        "--fix"
    ]
    
    log_info(f"Running ruff fix: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
        if result.returncode != 0:
            # Ruff returns non-zero if fixes were applied but some issues remain
            log_info("Ruff fix completed (some issues may remain).")
            logger.info(result.stdout)
        else:
            log_info("Ruff fix completed successfully.")
        return 0
    except Exception as e:
        log_error(f"Failed to run ruff fix: {e}")
        return 1

def run_black_check() -> int:
    """Run black check on the project.
    
    Returns:
        0 if check passes, non-zero otherwise.
    """
    project_root = get_project_root()
    cmd = [
        sys.executable, "-m", "black", 
        "--check",
        "--config", str(project_root / "pyproject.toml"),
        str(project_root)
    ]
    
    log_info(f"Running black check: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
        if result.returncode != 0:
            log_error("Black check failed (files need formatting):")
            logger.error(result.stdout)
        else:
            log_info("Black check passed.")
        return result.returncode
    except Exception as e:
        log_error(f"Failed to run black check: {e}")
        return 1

def run_black_format() -> int:
    """Run black formatter on the project.
    
    Returns:
        0 if successful, non-zero otherwise.
    """
    project_root = get_project_root()
    cmd = [
        sys.executable, "-m", "black", 
        "--config", str(project_root / "pyproject.toml"),
        str(project_root)
    ]
    
    log_info(f"Running black format: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
        if result.returncode != 0:
            log_error("Black format failed:")
            logger.error(result.stderr)
        else:
            log_info("Black format completed.")
        return result.returncode
    except Exception as e:
        log_error(f"Failed to run black format: {e}")
        return 1

def main():
    """Main entry point for linting configuration execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run linting and formatting tools.")
    parser.add_argument(
        "--mode", 
        choices=["check", "fix", "format"], 
        default="check",
        help="Mode of operation: check (lint only), fix (auto-fix lint), format (black only)"
    )
    
    args = parser.parse_args()
    
    project_root = get_project_root()
    log_info(f"Project root: {project_root}")
    
    exit_code = 0
    
    if args.mode == "check":
        # Run ruff check and black check
        ruff_code = run_ruff_check()
        black_code = run_black_check()
        exit_code = max(ruff_code, black_code)
        
    elif args.mode == "fix":
        # Run ruff fix and black check (black doesn't auto-fix in a way that leaves errors usually, but we format)
        run_ruff_fix()
        black_code = run_black_format() # Actually format with black
        exit_code = black_code
        
    elif args.mode == "format":
        # Run black format only
        exit_code = run_black_format()
        
    sys.exit(exit_code)

if __name__ == "__main__":
    main()