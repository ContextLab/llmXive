"""
Linting configuration and validation utilities.

This module provides functions to generate configuration files for 
flake8 and black, and to run linting checks.
"""
import os
import subprocess
import sys
from pathlib import Path
from typing import Tuple, Optional
import tempfile
import shutil


def create_black_config_file(output_path: Optional[str] = None) -> str:
    """
    Create a pyproject.toml file with Black configuration.
    
    Args:
        output_path: Optional path to write the config file. 
                     If None, writes to code/pyproject.toml
                     
    Returns:
        Path to the created configuration file
    """
    if output_path is None:
        output_path = str(Path("code") / "pyproject.toml")
    
    config_content = """[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310', 'py311']
include = '\\.pyi?$'
exclude = '''
/(
    \\.git
  | \\.hg
  | \\.mypy_cache
  | \\.tox
  | \\.venv
  | _build
  | buck-out
  | build
  | dist
  | venv
)/
'''
"""
    
    Path(output_path).write_text(config_content)
    return output_path


def create_flake8_config_file(output_path: Optional[str] = None) -> str:
    """
    Create a .flake8 file with configuration.
    
    Args:
        output_path: Optional path to write the config file.
                     If None, writes to code/.flake8
                     
    Returns:
        Path to the created configuration file
    """
    if output_path is None:
        output_path = str(Path("code") / ".flake8")
    
    config_content = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git,__pycache__,build,dist,.venv,venv
per-file-ignores =
    code/dataset/generator.py:E501
    code/analysis/stats.py:E501
    code/bes/population.py:E501
count = True
show-source = True
statistics = True
"""
    
    Path(output_path).write_text(config_content)
    return output_path


def run_black_check(path: str = "code", check_only: bool = True) -> Tuple[bool, str]:
    """
    Run Black formatting check on the code directory.
    
    Args:
        path: Directory or file path to check
        check_only: If True, only check formatting (don't modify)
                    
    Returns:
        Tuple of (success: bool, message: str)
    """
    cmd = ["black", "--check"] if check_only else ["black"]
    cmd.append(path)
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return True, "All files are formatted correctly."
        else:
            return False, f"Black formatting issues found:\n{result.stdout}\n{result.stderr}"
            
    except FileNotFoundError:
        return False, "Black is not installed. Run: pip install black"
    except subprocess.TimeoutExpired:
        return False, "Black check timed out."
    except Exception as e:
        return False, f"Error running Black: {str(e)}"


def run_flake8_check(path: str = "code") -> Tuple[bool, str]:
    """
    Run flake8 linting check on the code directory.
    
    Args:
        path: Directory or file path to check
                    
    Returns:
        Tuple of (success: bool, message: str)
    """
    cmd = ["flake8", path]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return True, "No linting issues found."
        else:
            return False, f"Linting issues found:\n{result.stdout}\n{result.stderr}"
            
    except FileNotFoundError:
        return False, "Flake8 is not installed. Run: pip install flake8"
    except subprocess.TimeoutExpired:
        return False, "Flake8 check timed out."
    except Exception as e:
        return False, f"Error running Flake8: {str(e)}"


def setup_linting() -> Tuple[bool, str]:
    """
    Set up linting configuration files in the project.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # Create configuration files
        black_path = create_black_config_file()
        flake8_path = create_flake8_config_file()
        
        return True, f"Linting configuration created:\n- Black: {black_path}\n- Flake8: {flake8_path}"
        
    except Exception as e:
        return False, f"Failed to set up linting configuration: {str(e)}"


def main() -> int:
    """
    Main entry point for linting setup and checks.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print("Setting up linting configuration...")
    success, message = setup_linting()
    print(message)
    
    if not success:
        return 1
    
    print("\nRunning Black check...")
    black_success, black_message = run_black_check()
    print(black_message)
    
    print("\nRunning Flake8 check...")
    flake8_success, flake8_message = run_flake8_check()
    print(flake8_message)
    
    if black_success and flake8_success:
        print("\n✓ All linting checks passed!")
        return 0
    else:
        print("\n✗ Some linting checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())