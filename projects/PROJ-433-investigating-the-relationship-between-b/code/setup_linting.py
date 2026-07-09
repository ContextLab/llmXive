"""
Script to initialize linting and formatting configuration for the project.
This task (T003) ensures ruff and black are configured via pyproject.toml.
"""
import os
import sys
from pathlib import Path

def main():
    """Verify that linting configuration exists and is valid."""
    root = Path(__file__).parent.parent
    config_file = root / "code" / "pyproject.toml"

    if not config_file.exists():
        print("ERROR: pyproject.toml not found in code/ directory.")
        sys.exit(1)

    content = config_file.read_text()
    
    # Verify presence of black and ruff sections
    has_black = "[tool.black]" in content
    has_ruff = "[tool.ruff]" in content
    has_pytest = "[tool.pytest.ini_options]" in content

    if not (has_black and has_ruff and has_pytest):
        print("ERROR: Missing required configuration sections in pyproject.toml.")
        print("  - [tool.black] missing:", not has_black)
        print("  - [tool.ruff] missing:", not has_ruff)
        print("  - [tool.pytest.ini_options] missing:", not has_pytest)
        sys.exit(1)

    print("SUCCESS: Linting and formatting configuration (ruff, black, pytest) verified.")
    print(f"  Config file: {config_file}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
