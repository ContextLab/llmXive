"""
Setup script to initialize linting and formatting tools configuration.
This script ensures that .flake8 and pyproject.toml are correctly configured
for the project's Python environment.
"""
import os
import sys

def verify_config_files():
    """Verify that linting configuration files exist in the code directory."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    flake8_config = os.path.join(base_dir, ".flake8")
    black_config = os.path.join(base_dir, "pyproject.toml")

    missing = []
    if not os.path.exists(flake8_config):
        missing.append(".flake8")
    if not os.path.exists(black_config):
        missing.append("pyproject.toml")

    if missing:
        print(f"Error: Missing configuration files: {', '.join(missing)}")
        print("Please ensure these files are created before running linting.")
        return False

    print("Linting configuration verified successfully.")
    return True

if __name__ == "__main__":
    if verify_config_files():
        print("Ready to run: flake8 .")
        print("Ready to run: black .")
        print("Ready to run: isort .")
        sys.exit(0)
    else:
        sys.exit(1)