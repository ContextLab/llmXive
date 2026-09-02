"""Setup and validation of linting configurations."""
import os
import sys
import subprocess
import tomli
from pathlib import Path

def check_file_exists(filepath: Path) -> bool:
    """Check if a file exists."""
    return filepath.exists()

def validate_black_config(project_root: Path) -> bool:
    """Validate Black configuration in pyproject.toml."""
    pyproject_path = project_root / "pyproject.toml"
    if not check_file_exists(pyproject_path):
        print(f"Error: {pyproject_path} not found.")
        return False

    try:
        with open(pyproject_path, "rb") as f:
            config = tomli.load(f)
        
        if "tool" not in config or "black" not in config["tool"]:
            print("Warning: [tool.black] section not found in pyproject.toml.")
            return False
        
        # Basic validation: ensure max-line-length is reasonable
        black_config = config["tool"]["black"]
        max_line_length = black_config.get("line-length", 88)
        if not isinstance(max_line_length, int) or max_line_length < 80 or max_line_length > 120:
            print(f"Warning: line-length {max_line_length} is outside recommended range [80, 120].")
            return False
        
        print("Black configuration is valid.")
        return True
    except Exception as e:
        print(f"Error validating Black config: {e}")
        return False

def validate_flake8_config(project_root: Path) -> bool:
    """Validate Flake8 configuration in .flake8."""
    flake8_path = project_root / ".flake8"
    if not check_file_exists(flake8_path):
        print(f"Error: {flake8_path} not found.")
        return False

    try:
        # Run flake8 --show-source to check if it can parse the config
        result = subprocess.run(
            ["flake8", "--config", str(flake8_path), "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            print(f"Error running flake8 with config: {result.stderr}")
            return False
        
        print("Flake8 configuration is valid.")
        return True
    except Exception as e:
        print(f"Error validating Flake8 config: {e}")
        return False

def main():
    """Main entry point for linting setup validation."""
    project_root = Path(__file__).resolve().parent.parent
    print(f"Validating linting configuration at: {project_root}")

    black_valid = validate_black_config(project_root)
    flake8_valid = validate_flake8_config(project_root)

    if black_valid and flake8_valid:
        print("All linting configurations are valid.")
        return 0
    else:
        print("Some linting configurations are invalid.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
