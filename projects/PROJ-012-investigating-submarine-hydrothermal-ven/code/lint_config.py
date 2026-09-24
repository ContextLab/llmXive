"""
Linting and Formatting Configuration and Execution Module.

This module provides functions to ensure ruff and black configurations exist,
and to run linting, formatting, and import sorting (isort) on the project codebase.
"""

import os
import subprocess
import sys
from pathlib import Path

try:
    import tomli
    import tomli_w
except ImportError:
    print("Error: 'tomli' and 'tomli_w' are required for config management. "
          "Please install them: pip install tomli tomli_w")
    sys.exit(1)


def ensure_ruff_config() -> Path:
    """
    Ensure a valid .ruff.toml configuration file exists in the project root.
    If it doesn't exist, create a default one.
    
    Returns:
        Path: The path to the ruff config file.
    """
    config_path = Path("pyproject.toml")
    default_config = {
        "tool": {
            "ruff": {
                "line-length": 88,
                "target-version": "py311",
                "select": [
                    "E",   # pycodestyle errors
                    "W",   # pycodestyle warnings
                    "F",   # Pyflakes
                    "I",   # isort
                    "C",   # flake8-comprehensions
                    "B",   # flake8-bugbear
                ],
                "ignore": [
                    "E501", # line too long (handled by black)
                    "B008", # do not perform function calls in argument defaults
                ],
                "exclude": [
                    ".git",
                    "__pycache__",
                    ".tox",
                    "build",
                    "dist",
                    ".eggs",
                    "*.egg-info",
                ],
                "per-file-ignores": {
                    "tests/*": ["E501", "S101"], # Allow assert in tests
                },
            }
        }
    }

    if not config_path.exists():
        print(f"Creating default ruff configuration at {config_path}...")
        with open(config_path, "wb") as f:
            tomli_w.dump(default_config, f)
        return config_path

    # Verify it has ruff config, if not, update it
    try:
        with open(config_path, "rb") as f:
            config = tomli.load(f)
        
        if "tool" not in config or "ruff" not in config["tool"]:
            print(f"Updating {config_path} with ruff configuration...")
            config["tool"] = config.get("tool", {})
            config["tool"]["ruff"] = default_config["tool"]["ruff"]
            with open(config_path, "wb") as f:
                tomli_w.dump(config, f)
    except Exception as e:
        print(f"Warning: Could not read/update {config_path}: {e}")
        # Fallback to creating a separate .ruff.toml
        ruff_path = Path(".ruff.toml")
        if not ruff_path.exists():
            with open(ruff_path, "w") as f:
                f.write("# Default Ruff Configuration\n")
                f.write("line-length = 88\n")
                f.write("target-version = \"py311\"\n")
            return ruff_path
        
    return config_path


def ensure_black_config() -> Path:
    """
    Ensure a valid black configuration exists in the project root (usually in pyproject.toml).
    
    Returns:
        Path: The path to the config file.
    """
    config_path = Path("pyproject.toml")
    default_black_config = {
        "tool": {
            "black": {
                "line-length": 88,
                "target-version": ["py311"],
                "include": r"code/.*\.py$",
                "exclude": r"/(\.git|\.tox|build|dist|\.eggs|.*\.egg-info)/",
            }
        }
    }

    if not config_path.exists():
        print(f"Creating default black configuration at {config_path}...")
        with open(config_path, "wb") as f:
            tomli_w.dump(default_black_config, f)
        return config_path

    try:
        with open(config_path, "rb") as f:
            config = tomli.load(f)
        
        if "tool" not in config or "black" not in config["tool"]:
            print(f"Updating {config_path} with black configuration...")
            config["tool"] = config.get("tool", {})
            config["tool"]["black"] = default_black_config["tool"]["black"]
            with open(config_path, "wb") as f:
                tomli_w.dump(config, f)
    except Exception as e:
        print(f"Warning: Could not read/update {config_path}: {e}")

    return config_path


def run_isort() -> int:
    """
    Run isort to sort imports.
    
    Returns:
        int: Return code (0 for success).
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "isort", "code/", "tests/"],
            check=True,
            capture_output=True,
            text=True
        )
        print("isort output:")
        print(result.stdout)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"isort error: {e.stderr}")
        return e.returncode
    except FileNotFoundError:
        print("Error: 'isort' not found. Please install it: pip install isort")
        return 1


def run_lint() -> int:
    """
    Run ruff linter.
    
    Returns:
        int: Return code (0 for success).
    """
    ensure_ruff_config()
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "code/", "tests/"],
            check=False, # We want to see the output even if there are errors
            capture_output=True,
            text=True
        )
        print("Ruff Lint Output:")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return result.returncode
    except FileNotFoundError:
        print("Error: 'ruff' not found. Please install it: pip install ruff")
        return 1


def run_format() -> int:
    """
    Run black formatter.
    
    Returns:
        int: Return code (0 for success).
    """
    ensure_black_config()
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "code/", "tests/"],
            check=False,
            capture_output=True,
            text=True
        )
        print("Black Format Output:")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return result.returncode
    except FileNotFoundError:
        print("Error: 'black' not found. Please install it: pip install black")
        return 1


def main():
    """
    Main entry point for running linting and formatting tools.
    """
    print("=== Linting and Formatting Configuration ===")
    
    # Ensure configs exist
    ensure_ruff_config()
    ensure_black_config()
    
    print("\n--- Running isort ---")
    isort_code = run_isort()
    
    print("\n--- Running Black ---")
    black_code = run_format()
    
    print("\n--- Running Ruff Lint ---")
    ruff_code = run_lint()
    
    if isort_code == 0 and black_code == 0 and ruff_code == 0:
        print("\n✅ All linting and formatting checks passed!")
        return 0
    else:
        print("\n❌ Some checks failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
