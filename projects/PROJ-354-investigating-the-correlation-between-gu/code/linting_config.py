import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

def get_black_config() -> Dict[str, Any]:
    """
    Returns the configuration dictionary for Black formatter.
    Matches standard project defaults: line length 88, target Python 3.10.
    """
    return {
        "line_length": 88,
        "target_version": "py310",
        "preview": True,
    }

def get_ruff_config() -> Dict[str, Any]:
    """
    Returns the configuration dictionary for Ruff linter.
    Includes standard rules: E (pycodestyle), F (pyflakes), I (isort), UP (pyupgrade).
    """
    return {
        "line-length": 88,
        "target-version": "py310",
        "select": [
            "E",  # pycodestyle errors
            "W",  # pycodestyle warnings
            "F",  # pyflakes
            "I",  # isort
            "B",  # flake8-bugbear
            "C4", # flake8-comprehensions
            "UP", # pyupgrade
        ],
        "ignore": [
            "E501", # Line too long (handled by Black)
            "B008", # Do not perform function call in argument defaults (common in dataclasses)
        ],
    }

def run_formatter(file_path: Optional[str] = None) -> bool:
    """
    Runs Black formatter on the project or specific file.
    
    Args:
        file_path: Optional specific file to format. If None, formats the 'code/' directory.
    
    Returns:
        True if formatting succeeded (exit code 0), False otherwise.
    """
    target = file_path if file_path else "code/"
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--config", "pyproject.toml", target],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode != 0:
            # Black returns 1 if files were changed, 0 if already formatted
            # We consider 0 or 1 as success for the action of running it
            if result.returncode == 1:
                return True 
            print(f"Black formatting failed for {target}: {result.stderr}")
            return False
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running Black: {e}")
        return False
    except FileNotFoundError:
        print("Error: Black not found. Ensure 'black' is installed.")
        return False

def run_linter(file_path: Optional[str] = None) -> bool:
    """
    Runs Ruff linter on the project or specific file.
    
    Args:
        file_path: Optional specific file to lint. If None, lints the 'code/' directory.
    
    Returns:
        True if linter passed (no errors), False otherwise.
    """
    target = file_path if file_path else "code/"
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "--config", "pyproject.toml", target],
            capture_output=True,
            text=True,
            check=False
        )
        # Ruff returns 0 if clean, 1 if issues found
        if result.returncode != 0:
            print(f"Ruff found issues in {target}:")
            print(result.stdout)
            if result.stderr:
                print(result.stderr)
            return False
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running Ruff: {e}")
        return False
    except FileNotFoundError:
        print("Error: Ruff not found. Ensure 'ruff' is installed.")
        return False

def validate_environment() -> bool:
    """
    Validates that linting and formatting tools are installed and accessible.
    
    Returns:
        True if both 'black' and 'ruff' are available, False otherwise.
    """
    tools = ["black", "ruff"]
    for tool in tools:
        try:
            subprocess.run(
                [sys.executable, "-m", tool, "--version"],
                capture_output=True,
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"Validation failed: '{tool}' is not installed or not in PATH.")
            return False
    print("Environment validation passed: All linting/formatting tools available.")
    return True
