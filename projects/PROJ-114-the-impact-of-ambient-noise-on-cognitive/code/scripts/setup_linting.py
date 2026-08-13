"""
Script to configure and verify linting (flake8) and formatting (black) tools.
This script ensures configuration files exist and dependencies are installed.
"""
import os
import sys
import configparser
import toml
from pathlib import Path

# Project root detection
ROOT_DIR = Path(__file__).parent.parent.parent
CONFIG_DIR = ROOT_DIR
REQUIREMENTS_FILE = ROOT_DIR / "requirements.txt"

def check_config_files():
    """Check if linting and formatting config files exist, create if missing."""
    files_to_check = {
        ".flake8": """[flake8]
max-line-length = 88
extend-ignore = E203, E501
exclude = .git,__pycache__,build,dist,.eggs
per-file-ignores =
    __init__.py:F401
""",
        "pyproject.toml": None,  # We will check/modify existing or create
    }

    # Handle .flake8
    flake8_path = CONFIG_DIR / ".flake8"
    if not flake8_path.exists():
        with open(flake8_path, "w") as f:
            f.write(files_to_check[".flake8"])
        print(f"Created {flake8_path}")
    else:
        print(f"Found existing {flake8_path}")

    # Handle pyproject.toml (for Black)
    pyproject_path = CONFIG_DIR / "pyproject.toml"
    if not pyproject_path.exists():
        # Create a basic pyproject.toml with black config
        black_config = """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "llmxive-project"
version = "0.1.0"
requires-python = ">=3.11"

[tool.black]
line-length = 88
target-version = ['py311']
skip-string-normalization = false

[tool.isort]
profile = "black"
line_length = 88
"""
        with open(pyproject_path, "w") as f:
            f.write(black_config)
        print(f"Created {pyproject_path} with Black configuration")
    else:
        # Check if Black section exists, if not, append or warn
        try:
            with open(pyproject_path, "r") as f:
                content = f.read()
            if "[tool.black]" not in content:
                # Append black config to existing file
                with open(pyproject_path, "a") as f:
                    f.write("\n[tool.black]\nline-length = 88\ntarget-version = ['py311']\n")
                print(f"Added Black configuration to existing {pyproject_path}")
            else:
                print(f"Found existing Black configuration in {pyproject_path}")
        except Exception as e:
            print(f"Warning: Could not verify pyproject.toml: {e}")

    return True

def check_requirements():
    """Check if flake8, black, and isort are in requirements.txt."""
    if not REQUIREMENTS_FILE.exists():
        print(f"Warning: {REQUIREMENTS_FILE} not found. Creating with linting tools.")
        with open(REQUIREMENTS_FILE, "w") as f:
            f.write("flake8>=6.0\nblack>=23.0\nisort>=5.12\n")
        return True

    with open(REQUIREMENTS_FILE, "r") as f:
        content = f.read().lower()

    missing = []
    if "flake8" not in content:
        missing.append("flake8")
    if "black" not in content:
        missing.append("black")
    if "isort" not in content:
        missing.append("isort")

    if missing:
        print(f"Adding missing linting tools to {REQUIREMENTS_FILE}: {missing}")
        with open(REQUIREMENTS_FILE, "a") as f:
            for pkg in missing:
                f.write(f"{pkg}\n")
        return True
    
    print(f"All linting tools found in {REQUIREMENTS_FILE}")
    return True

def main():
    """Main entry point to configure linting."""
    print("Configuring linting and formatting tools...")
    
    if not check_config_files():
        print("Failed to check/create config files.")
        sys.exit(1)
    
    if not check_requirements():
        print("Failed to update requirements.")
        sys.exit(1)

    print("Linting configuration complete.")
    print("To run flake8: flake8 code/")
    print("To run black: black code/")
    print("To run isort: isort code/")

if __name__ == "__main__":
    main()