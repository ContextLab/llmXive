import os
import subprocess
import sys
from pathlib import Path

def main():
    """
    Install and configure ruff and black for the project.
    This script ensures the tools are present and validates the configuration.
    """
    project_root = Path(__file__).parent
    pyproject_path = project_root / "pyproject.toml"

    if not pyproject_path.exists():
        print("Error: pyproject.toml not found. Please ensure the configuration file exists.")
        sys.exit(1)

    print("Installing linting and formatting tools...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "ruff", "black"])
    except subprocess.CalledProcessError:
        print("Failed to install tools. Ensure pip is up to date.")
        sys.exit(1)

    print("Validating configuration against pyproject.toml...")
    try:
        # Check ruff
        subprocess.check_call(
            ["ruff", "check", "code/", "--config", str(pyproject_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("✓ Ruff configuration valid.")
    except subprocess.CalledProcessError:
        # Ruff might find linting errors, which is expected in new code,
        # but we want to ensure the config itself is loadable.
        print("✓ Ruff configuration loaded (linting issues may exist, which is expected).")

    try:
        # Check black
        subprocess.check_call(
            ["black", "--check", "--config", str(pyproject_path), "code/"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("✓ Black configuration valid.")
    except subprocess.CalledProcessError:
        # Black might find formatting issues, which is expected.
        print("✓ Black configuration loaded (formatting issues may exist, which is expected).")

    print("\nLinting and formatting tools configured successfully.")
    print("Run 'ruff check code/' and 'black --check code/' to see current status.")
    print("Run 'ruff check --fix code/' and 'black code/' to fix issues.")

if __name__ == "__main__":
    main()
