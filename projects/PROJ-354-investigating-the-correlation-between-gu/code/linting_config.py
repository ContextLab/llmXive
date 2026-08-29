"""
Linting and formatting configuration management for llmXive project.

This module provides functions to generate and manage configuration
files for Black (formatter) and Ruff (linter), as well as utilities
to run these tools on the codebase.
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import logging

# Configure logging
logger = logging.getLogger(__name__)

def get_black_config() -> Dict[str, Any]:
    """
    Generate Black configuration dictionary.
    
    Returns:
        Dict containing Black configuration options.
    """
    return {
        "line-length": 88,
        "target-version": ["py310"],
        "include": r'\.pyi?$',
        "exclude": r'/(venv|\.venv|build|dist|\.git|__pycache__)/',
        "skip-string-normalization": False,
        "skip-magic-trailing-comma": False,
    }

def get_ruff_config() -> Dict[str, Any]:
    """
    Generate Ruff configuration dictionary.
    
    Returns:
        Dict containing Ruff configuration options.
    """
    return {
        "select": [
            "E",  # pycodestyle errors
            "F",  # Pyflakes
            "W",  # pycodestyle warnings
            "I",  # isort
        ],
        "ignore": [],
        "line-length": 88,
        "target-version": "py310",
        "exclude": [
            "venv",
            ".venv",
            "build",
            "dist",
            ".git",
            "__pycache__",
            "*.pyc",
        ],
        "per-file-ignores": {},
    }

def validate_environment() -> bool:
    """
    Check if required linting tools are installed.
    
    Returns:
        True if all required tools are available, False otherwise.
    """
    tools = ["black", "ruff"]
    missing = []
    
    for tool in tools:
        try:
            result = subprocess.run(
                [tool, "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"{tool} is installed: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append(tool)
            logger.warning(f"{tool} is not installed or not in PATH")
    
    if missing:
        logger.error(f"Missing required tools: {', '.join(missing)}")
        logger.info("Install missing tools with: pip install " + " ".join(missing))
        return False
    
    return True

def run_formatter(file_paths: Optional[List[str]] = None) -> bool:
    """
    Run Black formatter on specified files or the entire project.
    
    Args:
        file_paths: Optional list of file paths to format. If None, formats entire project.
        
    Returns:
        True if formatting succeeded, False otherwise.
    """
    try:
        cmd = ["black", "--config", str(Path(__file__).parent / "pyproject.toml")]
        if file_paths:
            cmd.extend(file_paths)
        else:
            # Format all Python files in the project
            project_root = Path(__file__).parent.parent
            cmd.append(str(project_root))
        
        logger.info(f"Running Black formatter: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        if result.stdout:
            logger.info(result.stdout)
        if result.stderr:
            logger.info(result.stderr)
        
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Black formatting failed: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during formatting: {e}")
        return False

def run_linter(file_paths: Optional[List[str]] = None) -> bool:
    """
    Run Ruff linter on specified files or the entire project.
    
    Args:
        file_paths: Optional list of file paths to lint. If None, lints entire project.
        
    Returns:
        True if linting passed (no errors), False otherwise.
    """
    try:
        cmd = ["ruff", "check", "--config", str(Path(__file__).parent / "pyproject.toml")]
        if file_paths:
            cmd.extend(file_paths)
        else:
            # Lint all Python files in the project
            project_root = Path(__file__).parent.parent
            cmd.append(str(project_root))
        
        logger.info(f"Running Ruff linter: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        if result.stdout:
            logger.info(result.stdout)
        if result.stderr:
            logger.info(result.stderr)
        
        return True
    except subprocess.CalledProcessError as e:
        # Ruff returns non-zero exit code when issues are found
        logger.warning(f"Ruff found issues:\n{e.stdout}")
        if e.stderr:
            logger.warning(f"Ruff stderr:\n{e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during linting: {e}")
        return False

def init_logging() -> None:
    """Initialize logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def main() -> int:
    """
    Main entry point for linting configuration and execution.
    
    Returns:
        Exit code: 0 for success, 1 for failure.
    """
    init_logging()
    
    # Validate that tools are installed
    if not validate_environment():
        logger.error("Required linting tools are not installed. Exiting.")
        return 1
    
    # Generate configuration files
    project_root = Path(__file__).parent
    
    # Create .ruff.toml
    ruff_config = get_ruff_config()
    ruff_path = project_root / ".ruff.toml"
    with open(ruff_path, "w") as f:
        f.write("# Ruff configuration\n")
        f.write(f"select = {ruff_config['select']}\n")
        f.write(f"ignore = {ruff_config['ignore']}\n")
        f.write(f"line-length = {ruff_config['line-length']}\n")
        f.write(f"target-version = '{ruff_config['target-version']}'\n")
        f.write(f"exclude = {ruff_config['exclude']}\n")
    logger.info(f"Created {ruff_path}")
    
    # Create pyproject.toml with Black configuration
    pyproject_path = project_root / "pyproject.toml"
    with open(pyproject_path, "w") as f:
        f.write("[tool.black]\n")
        f.write(f'line-length = {get_black_config()["line-length"]}\n')
        f.write(f'target-version = {get_black_config()["target-version"]}\n')
        f.write(f'include = "{get_black_config()["include"]}"\n')
        f.write(f'exclude = "{get_black_config()["exclude"]}"\n')
        f.write(f'skip-string-normalization = {get_black_config()["skip-string-normalization"]}\n')
        f.write(f'skip-magic-trailing-comma = {get_black_config()["skip-magic-trailing-comma"]}\n')
    logger.info(f"Created {pyproject_path}")
    
    # Run formatter
    logger.info("Running Black formatter...")
    if not run_formatter():
        logger.error("Black formatting failed. Please fix formatting issues manually.")
        return 1
    
    # Run linter
    logger.info("Running Ruff linter...")
    if not run_linter():
        logger.warning("Ruff found issues. Please review and fix them.")
        # Return 0 even if linter finds issues, as this is informational
        # but log the issues for the developer to fix
    
    logger.info("Linting and formatting completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
