"""
Configuration management for linting (ruff) and formatting (black) tools.
Ensures project-level configuration files exist and are consistent.
"""
import os
from pathlib import Path

def get_black_config_path() -> Path:
    """Return the path to the Black configuration."""
    return Path("pyproject.toml")

def get_ruff_config_path() -> Path:
    """Return the path to the Ruff configuration."""
    return Path("pyproject.toml")

def write_config_files() -> None:
    """
    Ensure configuration files for Black and Ruff exist.
    For this project, both are configured in pyproject.toml.
    This function validates that the file exists and contains the necessary sections.
    """
    project_root = Path.cwd()
    pyproject_path = project_root / "pyproject.toml"

    if not pyproject_path.exists():
        raise FileNotFoundError(
            f"pyproject.toml not found at {pyproject_path}. "
            "Please run the project initialization first."
        )

    content = pyproject_path.read_text()

    required_sections = ["[tool.black]", "[tool.ruff]"]
    missing_sections = [section for section in required_sections if section not in content]

    if missing_sections:
        raise ValueError(
            f"pyproject.toml is missing required sections: {missing_sections}. "
            "Please ensure Black and Ruff configurations are present."
        )

    print(f"Linting and formatting configuration validated at {pyproject_path}")

def main() -> int:
    """Entry point for linting configuration validation."""
    try:
        write_config_files()
        print("SUCCESS: Linting (ruff) and formatting (black) tools are configured.")
        return 0
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}")
        return 1

if __name__ == "__main__":
    exit(main())