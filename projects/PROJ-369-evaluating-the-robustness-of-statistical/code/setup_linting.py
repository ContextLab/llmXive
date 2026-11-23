"""
Setup script to validate linting and formatting tool configuration.
This script ensures that ruff and black are installed and that
the pyproject.toml configuration is valid.
"""
import os
import subprocess
import sys
from pathlib import Path


def check_file_exists(filepath: str) -> bool:
    """Check if a file exists in the project root."""
    return os.path.exists(filepath)


def check_black_installed() -> bool:
    """Check if black is installed and available."""
    try:
        subprocess.run(
            ["black", "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_ruff_installed() -> bool:
    """Check if ruff is installed and available."""
    try:
        subprocess.run(
            ["ruff", "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def validate_config() -> bool:
    """Validate the pyproject.toml configuration for black and ruff."""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        print("ERROR: pyproject.toml not found in project root.")
        return False

    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            print("ERROR: tomllib or tomli is required to parse pyproject.toml.")
            print("Install with: pip install tomli")
            return False

    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)

    errors = []

    if "tool" not in config or "black" not in config["tool"]:
        errors.append("Missing [tool.black] section in pyproject.toml")
    else:
        black_config = config["tool"]["black"]
        if "line-length" not in black_config:
            errors.append("Missing 'line-length' in [tool.black]")

    if "tool" not in config or "ruff" not in config["tool"]:
        errors.append("Missing [tool.ruff] section in pyproject.toml")
    else:
        ruff_config = config["tool"]["ruff"]
        if "line-length" not in ruff_config:
            errors.append("Missing 'line-length' in [tool.ruff]")
        if "select" not in ruff_config:
            errors.append("Missing 'select' rules in [tool.ruff]")

    if errors:
        print("Configuration validation errors:")
        for error in errors:
            print(f"  - {error}")
        return False

    return True


def main() -> int:
    """Main entry point for the setup script."""
    print("Setting up linting and formatting tools...")
    print("-" * 50)

    # Check for pyproject.toml
    if not check_file_exists("pyproject.toml"):
        print("ERROR: pyproject.toml not found. Please run the project initialization first.")
        return 1

    # Check tool installations
    print("Checking tool installations...")
    black_ok = check_black_installed()
    ruff_ok = check_ruff_installed()

    if not black_ok:
        print("WARNING: black is not installed. Install with: pip install black")
    else:
        print("✓ black is installed")

    if not ruff_ok:
        print("WARNING: ruff is not installed. Install with: pip install ruff")
    else:
        print("✓ ruff is installed")

    # Validate configuration
    print("\nValidating configuration...")
    config_ok = validate_config()
    if config_ok:
        print("✓ Configuration is valid")
    else:
        print("ERROR: Configuration validation failed")
        return 1

    print("-" * 50)
    print("Setup complete. You can now run:")
    print("  black .                 # Format code")
    print("  ruff check .            # Lint code")
    print("  pytest                  # Run tests")
    return 0


if __name__ == "__main__":
    sys.exit(main())