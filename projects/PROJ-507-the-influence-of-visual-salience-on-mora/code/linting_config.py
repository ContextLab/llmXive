"""
Configuration and execution helpers for Ruff and Black.
Ensures the project adheres to consistent linting and formatting standards.
"""
import subprocess
import sys
from pathlib import Path
from typing import Tuple, Optional


def run_ruff_check() -> Tuple[bool, str]:
    """Run ruff check on the codebase.

    Returns:
        Tuple of (success, message).
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "."],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return True, "Ruff check passed."
        return False, f"Ruff check failed:\n{result.stdout}\n{result.stderr}"
    except FileNotFoundError:
        return False, "Ruff is not installed. Run: pip install ruff"


def run_ruff_fix() -> Tuple[bool, str]:
    """Run ruff check --fix on the codebase.

    Returns:
        Tuple of (success, message).
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "--fix", "."],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return True, "Ruff fix completed."
        return False, f"Ruff fix issues remain:\n{result.stdout}\n{result.stderr}"
    except FileNotFoundError:
        return False, "Ruff is not installed. Run: pip install ruff"


def run_black_check() -> Tuple[bool, str]:
    """Run black --check on the codebase.

    Returns:
        Tuple of (success, message).
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "--check", "."],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return True, "Black check passed."
        return False, f"Black check failed:\n{result.stdout}\n{result.stderr}"
    except FileNotFoundError:
        return False, "Black is not installed. Run: pip install black"


def run_black_format() -> Tuple[bool, str]:
    """Run black formatting on the codebase.

    Returns:
        Tuple of (success, message).
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "black", "."],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return True, "Black formatting completed."
        return False, f"Black formatting failed:\n{result.stdout}\n{result.stderr}"
    except FileNotFoundError:
        return False, "Black is not installed. Run: pip install black"


def verify_tools_installed() -> Tuple[bool, str]:
    """Verify that ruff and black are installed.

    Returns:
        Tuple of (success, message).
    """
    missing = []
    try:
        subprocess.run(
            [sys.executable, "-m", "ruff", "--version"],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        missing.append("ruff")

    try:
        subprocess.run(
            [sys.executable, "-m", "black", "--version"],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        missing.append("black")

    if missing:
        return False, f"Missing tools: {', '.join(missing)}. Install with: pip install {' '.join(missing)}"
    return True, "All linting and formatting tools are installed."


def setup_config_files() -> Tuple[bool, str]:
    """Ensure configuration files exist in the project root.

    Returns:
        Tuple of (success, message).
    """
    root = Path(__file__).parent.parent
    ruff_config = root / ".ruff.toml"
    pyproject = root / "pyproject.toml"

    if not ruff_config.exists():
        return False, f"Missing config: {ruff_config}. Run the setup script to generate it."
    if not pyproject.exists():
        return False, f"Missing config: {pyproject}. Run the setup script to generate it."

    return True, "Configuration files are present."