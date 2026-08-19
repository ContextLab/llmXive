import os
import sys
from pathlib import Path

def check_file_exists(file_path: str) -> bool:
    """Check if a specific file exists in the project root."""
    return Path(file_path).exists()

def main() -> None:
    """
    Main entry point for the linting setup task.
    This script verifies that the necessary configuration files for
    linting (ruff) and formatting (black) exist in the project root.
    If they are missing, it prints a helpful error message and exits.
    """
    project_root = Path(__file__).parent.parent
    
    required_configs = [
        project_root / "pyproject.toml",
        project_root / ".flake8",
    ]

    missing_files = []
    for config_file in required_configs:
        if not config_file.exists():
            missing_files.append(config_file.name)

    if missing_files:
        print("Error: Linting/Formatting configuration files are missing.")
        print(f"Missing: {', '.join(missing_files)}")
        print("Please ensure 'pyproject.toml' (with [tool.black] and [tool.ruff]) "
              "and '.flake8' are present in the project root.")
        sys.exit(1)
    
    print("Linting and formatting configuration verified successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
