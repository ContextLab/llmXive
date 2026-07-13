"""
Utility script to verify linting and formatting tool configurations.
This script checks if ruff and black are installed and if their config files are valid.
"""
import subprocess
import sys
import tomllib
from pathlib import Path


def check_command_available(command: str) -> bool:
    """Check if a command is available in the system PATH."""
    try:
        subprocess.run(
            [command, "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def validate_config_files() -> dict:
    """
    Validate that configuration files for black and ruff exist and are parsable.
    Returns a dictionary with validation results.
    """
    results = {
        "black_config_valid": False,
        "ruff_config_valid": False,
        "errors": []
    }

    project_root = Path(__file__).resolve().parent.parent.parent

    # Check pyproject.toml for Black and Ruff configuration
    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.exists():
        results["errors"].append("pyproject.toml not found at project root")
        return results

    try:
        with open(pyproject_path, "rb") as f:
            config = tomllib.load(f)

        # Validate Black config
        if "tool" in config and "black" in config["tool"]:
            results["black_config_valid"] = True
        else:
            results["errors"].append("Black configuration missing in pyproject.toml")

        # Validate Ruff config
        if "tool" in config and "ruff" in config["tool"]:
            results["ruff_config_valid"] = True
        else:
            results["errors"].append("Ruff configuration missing in pyproject.toml")

    except tomllib.TOMLDecodeError as e:
        results["errors"].append(f"Failed to parse pyproject.toml: {e}")

    return results


def main():
    """Main entry point for the setup verification script."""
    print("Checking Linting and Formatting Tools Configuration...")
    print("-" * 50)

    # Check tools availability
    black_available = check_command_available("black")
    ruff_available = check_command_available("ruff")

    print(f"Black available: {black_available}")
    print(f"Ruff available: {ruff_available}")

    if not black_available or not ruff_available:
        print("\nWARNING: Tools are not installed. Run: pip install -e '.[dev]'")
        return 1

    # Validate configs
    validation = validate_config_files()

    if validation["errors"]:
        print("\nConfiguration Errors:")
        for error in validation["errors"]:
            print(f"  - {error}")
        return 1

    print("\nAll configuration files are valid.")
    print("To format code: black .")
    print("To lint code: ruff check .")
    return 0


if __name__ == "__main__":
    sys.exit(main())