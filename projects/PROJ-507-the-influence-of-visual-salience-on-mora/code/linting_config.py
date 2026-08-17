"""
Linting and Formatting Configuration Module.

Provides functions to verify and run ruff and black tools.
"""
import subprocess
import sys
from pathlib import Path
from typing import Tuple, Optional

from config import seed_everything

seed_everything(42)


def verify_tools_installed() -> Tuple[bool, str]:
    """
    Check if ruff and black are installed in the current environment.

    Returns:
        Tuple of (success: bool, message: str)
    """
    missing = []

    try:
        subprocess.run(["ruff", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        missing.append("ruff")

    try:
        subprocess.run(["black", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        missing.append("black")

    if missing:
        return False, f"Missing tools: {', '.join(missing)}. Install via: pip install {', '.join(missing)}"

    return True, "All linting and formatting tools are installed."


def run_ruff_check(path: Optional[Path] = None) -> Tuple[bool, str]:
    """
    Run ruff check on the project.

    Args:
        path: Specific path to check, or None for project root.

    Returns:
        Tuple of (success: bool, message: str)
    """
    target = path if path else Path(".")

    try:
        result = subprocess.run(
            ["ruff", "check", str(target)],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return True, "Ruff check passed."
        return False, f"Ruff check failed:\n{result.stdout}\n{result.stderr}"
    except FileNotFoundError:
        return False, "ruff not found. Install it with: pip install ruff"


def run_ruff_fix(path: Optional[Path] = None) -> Tuple[bool, str]:
    """
    Run ruff check with --fix to automatically fix issues.

    Args:
        path: Specific path to fix, or None for project root.

    Returns:
        Tuple of (success: bool, message: str)
    """
    target = path if path else Path(".")

    try:
        result = subprocess.run(
            ["ruff", "check", "--fix", str(target)],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return True, "Ruff fix completed successfully."
        return False, f"Ruff fix finished with remaining issues:\n{result.stdout}"
    except FileNotFoundError:
        return False, "ruff not found. Install it with: pip install ruff"


def run_black_check(path: Optional[Path] = None) -> Tuple[bool, str]:
    """
    Run black --check to verify formatting.

    Args:
        path: Specific path to check, or None for project root.

    Returns:
        Tuple of (success: bool, message: str)
    """
    target = path if path else Path(".")

    try:
        result = subprocess.run(
            ["black", "--check", str(target)],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return True, "Black formatting check passed."
        return False, f"Black formatting issues found:\n{result.stdout}"
    except FileNotFoundError:
        return False, "black not found. Install it with: pip install black"


def run_black_format(path: Optional[Path] = None) -> Tuple[bool, str]:
    """
    Run black to format code.

    Args:
        path: Specific path to format, or None for project root.

    Returns:
        Tuple of (success: bool, message: str)
    """
    target = path if path else Path(".")

    try:
        result = subprocess.run(
            ["black", str(target)],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return True, "Black formatting completed successfully."
        return False, f"Black formatting failed:\n{result.stderr}"
    except FileNotFoundError:
        return False, "black not found. Install it with: pip install black"


def setup_config_files() -> Tuple[bool, str]:
    """
    Ensure configuration files (.ruff.toml and pyproject.toml) exist.

    Returns:
        Tuple of (success: bool, message: str)
    """
    root = Path(".")
    ruff_config = root / ".ruff.toml"
    pyproject = root / "pyproject.toml"

    if not ruff_config.exists():
        return False, "Missing .ruff.toml configuration file."

    if not pyproject.exists():
        return False, "Missing pyproject.toml configuration file."

    return True, "Configuration files verified."


def main():
    """Main entry point for linting configuration verification."""
    import argparse

    parser = argparse.ArgumentParser(description="Linting and Formatting Tools")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run checks only (ruff check, black check)",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Run fix commands (ruff fix, black format)",
    )
    parser.add_argument(
        "--path",
        type=str,
        default=None,
        help="Target path (default: project root)",
    )
    args = parser.parse_args()

    target = Path(args.path) if args.path else None

    # Verify tools
    success, msg = verify_tools_installed()
    print(f"[INFO] {msg}")
    if not success:
        sys.exit(1)

    # Verify config files
    success, msg = setup_config_files()
    print(f"[INFO] {msg}")
    if not success:
        sys.exit(1)

    if args.check:
        # Run checks
        ruff_ok, ruff_msg = run_ruff_check(target)
        print(f"[RUFF] {ruff_msg}")
        black_ok, black_msg = run_black_check(target)
        print(f"[BLACK] {black_msg}")

        if not (ruff_ok and black_ok):
            sys.exit(1)
        print("[SUCCESS] All checks passed.")

    elif args.fix:
        # Run fixes
        ruff_ok, ruff_msg = run_ruff_fix(target)
        print(f"[RUFF] {ruff_msg}")
        black_ok, black_msg = run_black_format(target)
        print(f"[BLACK] {black_msg}")

        if not (ruff_ok and black_ok):
            sys.exit(1)
        print("[SUCCESS] All fixes applied.")
    else:
        print("[INFO] Use --check or --fix to run commands.")
        print("[INFO] Example: python code/linting_config.py --check")


if __name__ == "__main__":
    main()