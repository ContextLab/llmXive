"""
Linting and Formatting Configuration for llmXive project.

This module provides utilities to create configuration files for Black and Flake8,
and to run checks to ensure code quality standards are met.
"""
import os
import subprocess
import sys
from pathlib import Path
from typing import Tuple, Optional

# Project root is assumed to be the parent of 'code'
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def create_black_config_file(config_path: Optional[Path] = None) -> Path:
    """
    Creates a pyproject.toml file with Black configuration if it doesn't exist or doesn't contain Black config.

    Args:
        config_path: Optional path to the config file. Defaults to PROJECT_ROOT/pyproject.toml.

    Returns:
        Path to the created/updated configuration file.
    """
    if config_path is None:
        config_path = PROJECT_ROOT / "pyproject.toml"

    # Ensure the parent directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    black_config = """[tool.black]
line-length = 88
target-version = ['py311']
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
)/
'''
"""

    # Check if file exists and has [tool.black] section
    if config_path.exists():
        content = config_path.read_text()
        if "[tool.black]" in content:
            print(f"Black configuration already exists in {config_path}. Skipping creation.")
            return config_path

    # Write the configuration
    with open(config_path, "a") as f:
        f.write("\n" + black_config)

    print(f"Created/Updated Black configuration at {config_path}")
    return config_path


def create_flake8_config_file(config_path: Optional[Path] = None) -> Path:
    """
    Creates a .flake8 file with Flake8 configuration if it doesn't exist.

    Args:
        config_path: Optional path to the config file. Defaults to PROJECT_ROOT/.flake8.

    Returns:
        Path to the created configuration file.
    """
    if config_path is None:
        config_path = PROJECT_ROOT / ".flake8"

    flake8_config = """[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    build,
    dist,
    .venv,
    venv,
    *.egg-info
per-file-ignores =
    # Allow unused imports in __init__.py
    */__init__.py: F401
"""

    # Write the configuration (overwrite if exists to ensure consistency)
    with open(config_path, "w") as f:
        f.write(flake8_config)

    print(f"Created Flake8 configuration at {config_path}")
    return config_path


def run_black_check(path: Path, check_only: bool = True) -> Tuple[bool, str]:
    """
    Runs Black on the specified path.

    Args:
        path: The file or directory to check.
        check_only: If True, only checks formatting without modifying files.

    Returns:
        A tuple (success, message). success is True if formatting is correct (or --check passes).
    """
    cmd = ["black"]
    if check_only:
        cmd.append("--check")
    cmd.append(str(path))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        if result.returncode == 0:
            return True, "Black check passed."
        else:
            return False, f"Black check failed:\n{result.stdout}\n{result.stderr}"
    except FileNotFoundError:
        return False, "Black is not installed. Please run: pip install black"
    except Exception as e:
        return False, f"Error running Black: {str(e)}"


def run_flake8_check(path: Path) -> Tuple[bool, str]:
    """
    Runs Flake8 on the specified path.

    Args:
        path: The file or directory to check.

    Returns:
        A tuple (success, message). success is True if no linting errors found.
    """
    cmd = ["flake8", str(path)]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        if result.returncode == 0:
            return True, "Flake8 check passed."
        else:
            return False, f"Flake8 check failed:\n{result.stdout}\n{result.stderr}"
    except FileNotFoundError:
        return False, "Flake8 is not installed. Please run: pip install flake8"
    except Exception as e:
        return False, f"Error running Flake8: {str(e)}"


def setup_linting() -> Tuple[bool, str]:
    """
    Sets up linting and formatting configuration files for the project.

    Returns:
        A tuple (success, message).
    """
    try:
        create_black_config_file()
        create_flake8_config_file()
        return True, "Linting and formatting configuration created successfully."
    except Exception as e:
        return False, f"Failed to setup linting configuration: {str(e)}"


def main() -> int:
    """
    Main entry point for the linting configuration script.
    Creates config files and runs checks if dependencies are installed.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    print("Setting up linting and formatting configuration...")
    success, msg = setup_linting()
    print(msg)

    if not success:
        return 1

    print("\nRunning Black check...")
    black_success, black_msg = run_black_check(PROJECT_ROOT / "code")
    print(black_msg)

    print("\nRunning Flake8 check...")
    flake8_success, flake8_msg = run_flake8_check(PROJECT_ROOT / "code")
    print(flake8_msg)

    if black_success and flake8_success:
        print("\nAll checks passed!")
        return 0
    else:
        print("\nSome checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())