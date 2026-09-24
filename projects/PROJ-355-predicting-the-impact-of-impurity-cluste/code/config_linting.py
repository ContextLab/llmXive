"""
Configuration utilities for linting and formatting tools.
Handles creation and validation of ruff and black configuration.
"""
import os
import subprocess
import sys
from pathlib import Path

from config import get_project_root


def ensure_project_root() -> Path:
    """
    Ensure the project root directory exists.

    Returns:
        Path to the project root.

    Raises:
        FileNotFoundError: If project root is not found.
    """
    root = get_project_root()
    if not root.exists():
        raise FileNotFoundError(f"Project root not found: {root}")
    return root


def create_ruff_config(project_root: Path) -> bool:
    """
    Create or validate ruff configuration in pyproject.toml.

    Args:
        project_root: Path to the project root directory.

    Returns:
        True if configuration is valid, False otherwise.
    """
    pyproject_path = project_root / "pyproject.toml"

    if not pyproject_path.exists():
        print(f"✗ {pyproject_path} not found.")
        return False

    try:
        # Run ruff check to validate configuration
        result = subprocess.run(
            ["ruff", "check", "--config", str(pyproject_path), "--output-format=concise"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        # We expect exit code 1 if there are linting errors, 0 if clean
        # Exit code 2 or other indicates configuration error
        if result.returncode == 2:
            print(f"✗ Ruff configuration error:\n{result.stderr}")
            return False
        return True
    except FileNotFoundError:
        print("✗ Ruff not found. Please install it first.")
        return False


def create_black_config(project_root: Path) -> bool:
    """
    Create or validate black configuration in pyproject.toml.

    Args:
        project_root: Path to the project root directory.

    Returns:
        True if configuration is valid, False otherwise.
    """
    pyproject_path = project_root / "pyproject.toml"

    if not pyproject_path.exists():
        print(f"✗ {pyproject_path} not found.")
        return False

    try:
        # Run black --check to validate configuration
        result = subprocess.run(
            ["black", "--config", str(pyproject_path), "--check", "--diff", "."],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        # Exit code 0 = clean, 1 = needs formatting, 2 = config error
        if result.returncode == 2:
            print(f"✗ Black configuration error:\n{result.stderr}")
            return False
        return True
    except FileNotFoundError:
        print("✗ Black not found. Please install it first.")
        return False


def verify_tools(project_root: Path) -> bool:
    """
    Verify that ruff and black are installed and configured correctly.

    Args:
        project_root: Path to the project root directory.

    Returns:
        True if all tools are ready, False otherwise.
    """
    print("Verifying linting tools...")

    # Check ruff
    ruff_ok = create_ruff_config(project_root)
    if ruff_ok:
        print("✓ Ruff configuration valid.")
    else:
        print("✗ Ruff configuration invalid.")

    # Check black
    black_ok = create_black_config(project_root)
    if black_ok:
        print("✓ Black configuration valid.")
    else:
        print("✗ Black configuration invalid.")

    return ruff_ok and black_ok


def main() -> int:
    """
    Main entry point for linting configuration verification.

    Returns:
        0 on success, 1 on failure.
    """
    try:
        project_root = ensure_project_root()
    except FileNotFoundError as e:
        print(str(e))
        return 1

    if verify_tools(project_root):
        print("\n✓ All linting tools are ready.")
        return 0
    else:
        print("\n✗ Some linting tools are not ready.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
