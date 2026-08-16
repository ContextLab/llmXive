"""
Linting and formatting configuration for the llmXive project.

This module provides utilities to create and manage configuration files
for Black (code formatter) and Flake8 (linter), as well as functions
to run checks against the codebase.
"""
import os
import subprocess
import sys
from pathlib import Path
from typing import Tuple, Optional


def create_black_config_file(config_path: Optional[Path] = None) -> Path:
    """
    Creates a pyproject.toml file with Black configuration if one does not exist.

    Args:
        config_path: Optional path to the config file. Defaults to project root 'pyproject.toml'.

    Returns:
        The path to the created or existing config file.
    """
    if config_path is None:
        config_path = Path("pyproject.toml")

    # Check if it already exists to avoid overwriting
    if config_path.exists():
        # Simple check to see if [tool.black] exists
        content = config_path.read_text()
        if "[tool.black]" in content:
            return config_path

    # Define Black configuration
    black_config = """
[tool.black]
line-length = 88
target-version = ['py311']
include = 'code/.*\\.pyi?$'
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
    # Append if file exists, otherwise create
    if config_path.exists():
        with open(config_path, "a") as f:
            f.write(black_config)
    else:
        config_path.write_text(black_config)

    return config_path


def create_flake8_config_file(config_path: Optional[Path] = None) -> Path:
    """
    Creates a .flake8 configuration file if one does not exist.

    Args:
        config_path: Optional path to the config file. Defaults to project root '.flake8'.

    Returns:
        The path to the created or existing config file.
    """
    if config_path is None:
        config_path = Path(".flake8")

    if config_path.exists():
        return config_path

    flake8_config = """
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    build,
    dist,
    .venv,
    venv,
    .mypy_cache
per-file-ignores =
    # Allow unused imports in __init__.py
    */__init__.py:F401
"""
    config_path.write_text(flake8_config)
    return config_path


def run_black_check(path: Optional[Path] = None, check_only: bool = True) -> Tuple[bool, str]:
    """
    Runs Black on the specified path.

    Args:
        path: Directory or file to check. Defaults to current directory.
        check_only: If True, runs in 'check' mode (no writing). If False, reformats.

    Returns:
        Tuple of (success: bool, message: str).
    """
    cmd = [sys.executable, "-m", "black"]
    if check_only:
        cmd.append("--check")
        cmd.append("--diff")

    cmd.append("--quiet")
    if path:
        cmd.append(str(path))
    else:
        cmd.append("code")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0:
            return True, "Black check passed."
        else:
            return False, f"Black check failed:\n{result.stdout}\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return False, "Black check timed out."
    except Exception as e:
        return False, f"Error running Black: {str(e)}"


def run_flake8_check(path: Optional[Path] = None) -> Tuple[bool, str]:
    """
    Runs Flake8 on the specified path.

    Args:
        path: Directory or file to check. Defaults to current directory.

    Returns:
        Tuple of (success: bool, message: str).
    """
    cmd = [sys.executable, "-m", "flake8"]
    if path:
        cmd.append(str(path))
    else:
        cmd.append("code")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0:
            return True, "Flake8 check passed."
        else:
            return False, f"Flake8 check failed:\n{result.stdout}\n{result.stderr}"
    except subprocess.TimeoutExpired:
        return False, "Flake8 check timed out."
    except Exception as e:
        return False, f"Error running Flake8: {str(e)}"


def setup_linting(project_root: Optional[Path] = None) -> Tuple[Path, Path]:
    """
    Sets up linting configuration files for the project.

    Args:
        project_root: Path to the project root. Defaults to current directory.

    Returns:
        Tuple of (black_config_path, flake8_config_path).
    """
    if project_root is None:
        project_root = Path.cwd()

    os.chdir(project_root)

    black_cfg = create_black_config_file()
    flake8_cfg = create_flake8_config_file()

    return black_cfg, flake8_cfg


def main() -> int:
    """
    Main entry point for linting configuration and checks.

    Usage:
        python code/linting_config.py --setup
        python code/linting_config.py --check
        python code/linting_config.py --format

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    import argparse

    parser = argparse.ArgumentParser(description="Linting configuration and checks")
    parser.add_argument("--setup", action="store_true", help="Create config files")
    parser.add_argument("--check", action="store_true", help="Run checks only")
    parser.add_argument("--format", action="store_true", help="Format code (write changes)")
    parser.add_argument("--path", type=str, help="Path to check/format (default: code/)")

    args = parser.parse_args()

    if args.setup or (not args.check and not args.format):
        print("Setting up linting configuration...")
        black_cfg, flake8_cfg = setup_linting()
        print(f"Created/Updated: {black_cfg}")
        print(f"Created/Updated: {flake8_cfg}")

    if args.check or (not args.setup and not args.format):
        print("\nRunning Black check...")
        path = Path(args.path) if args.path else None
        success, msg = run_black_check(path, check_only=True)
        print(msg)
        if not success:
            print("Run 'python code/linting_config.py --format' to fix.")
            return 1

        print("\nRunning Flake8 check...")
        success, msg = run_flake8_check(path)
        print(msg)
        if not success:
            return 1

    if args.format:
        print("\nRunning Black formatter (writing changes)...")
        path = Path(args.path) if args.path else None
        # Black writes changes when --check is not passed
        cmd = [sys.executable, "-m", "black", str(path) if path else "code"]
        try:
            subprocess.run(cmd, check=True)
            print("Formatting complete.")
        except subprocess.CalledProcessError as e:
            print(f"Formatting failed: {e}")
            return 1

    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())