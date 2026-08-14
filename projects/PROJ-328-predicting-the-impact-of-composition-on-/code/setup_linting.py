import os
import sys
import subprocess
import tomli
from pathlib import Path

def check_file_exists(filepath):
    """Check if a file exists at the given path."""
    return Path(filepath).exists()

def validate_black_config(project_root):
    """Validate black configuration in pyproject.toml."""
    pyproject_path = project_root / "pyproject.toml"
    
    if not pyproject_path.exists():
        print("ERROR: pyproject.toml not found")
        return False

    try:
        with open(pyproject_path, "rb") as f:
            config = tomli.load(f)
        
        if "tool" not in config or "black" not in config["tool"]:
            print("WARNING: black configuration not found in pyproject.toml")
            return False

        black_config = config["tool"]["black"]
        print(f"Black configuration: {black_config}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to parse pyproject.toml: {e}")
        return False

def validate_flake8_config(project_root):
    """Validate flake8 configuration in .flake8 or setup.cfg."""
    flake8_config_path = project_root / ".flake8"
    setup_cfg_path = project_root / "setup.cfg"

    if flake8_config_path.exists():
        print("Found .flake8 configuration")
        return True
    elif setup_cfg_path.exists():
        print("Found setup.cfg configuration")
        return True
    else:
        print("WARNING: No flake8 configuration found")
        return False

def main():
    """Main entry point for linting configuration validation."""
    project_root = Path(__file__).resolve().parent.parent

    print("Validating linting configuration...")
    
    black_valid = validate_black_config(project_root)
    flake8_valid = validate_flake8_config(project_root)

    if black_valid and flake8_valid:
        print("Linting configuration is valid")
        return 0
    else:
        print("Linting configuration validation failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
