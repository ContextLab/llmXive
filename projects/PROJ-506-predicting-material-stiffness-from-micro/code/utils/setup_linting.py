"""
Utility script to configure and verify linting (ruff) and formatting (black).
This script ensures the project adheres to the coding standards defined in pyproject.toml.
"""
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple, Optional

def check_command_available(command: str) -> bool:
    """Check if a command is available in the system PATH."""
    try:
        subprocess.run(
            ["which", command],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False

def create_pyproject_config() -> None:
    """
    Ensure pyproject.toml exists with correct ruff and black configuration.
    If missing or incorrect, this function would ideally update it,
    but for this task, we assume the file is created by the implementer
    and we verify its existence.
    """
    root = Path(__file__).resolve().parent.parent
    config_file = root / "pyproject.toml"
    
    if not config_file.exists():
        raise FileNotFoundError(
            f"pyproject.toml not found at {config_file}. "
            "Please create the configuration file before running verification."
        )
    
    content = config_file.read_text()
    if "[tool.ruff]" not in content or "[tool.black]" not in content:
        raise ValueError(
            "pyproject.toml is missing [tool.ruff] or [tool.black] sections. "
            "Please update the configuration file."
        )

def validate_config_files() -> Tuple[bool, List[str]]:
    """
    Run ruff check and black --check to verify configuration.
    Returns (success, errors).
    """
    root = Path(__file__).resolve().parent.parent
    errors = []
    success = True

    # Check Ruff
    if not check_command_available("ruff"):
        errors.append("Ruff is not installed or not in PATH. Run: pip install ruff")
        success = False
    else:
        try:
            result = subprocess.run(
                ["ruff", "check", "."],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                errors.append(f"Ruff check failed:\n{result.stdout}\n{result.stderr}")
                success = False
            else:
                print("Ruff check passed.")
        except Exception as e:
            errors.append(f"Error running ruff: {e}")
            success = False

    # Check Black
    if not check_command_available("black"):
        errors.append("Black is not installed or not in PATH. Run: pip install black")
        success = False
    else:
        try:
            result = subprocess.run(
                ["black", "--check", "."],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                errors.append(f"Black check failed:\n{result.stdout}\n{result.stderr}")
                success = False
            else:
                print("Black check passed.")
        except Exception as e:
            errors.append(f"Error running black: {e}")
            success = False

    return success, errors

def main() -> int:
    """Main entry point for the linting setup script."""
    print("Verifying linting and formatting configuration...")
    
    try:
        create_pyproject_config()
        print("Configuration file validation passed.")
    except (FileNotFoundError, ValueError) as e:
        print(f"Configuration error: {e}")
        return 1

    success, errors = validate_config_files()
    
    if success:
        print("All linting and formatting checks passed.")
        return 0
    else:
        print("Linting/Formatting checks failed:")
        for err in errors:
            print(f" - {err}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
