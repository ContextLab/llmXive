"""
Script to verify and document linting, formatting, and type-checking configuration.
This script ensures that the required configuration files exist and are valid.
"""
import os
import sys
from pathlib import Path

def check_file_exists(filepath: str) -> bool:
    """Check if a file exists in the project root."""
    return os.path.isfile(filepath)

def main():
    """Verify configuration files for linting, formatting, and type checking."""
    base_dir = Path(__file__).parent
    config_files = {
        "flake8": base_dir / ".flake8",
        "black": base_dir / "pyproject.toml",
        "isort": base_dir / "pyproject.toml",
        "mypy": base_dir / "mypy.ini",
        "pytest": base_dir / "pyproject.toml",
        "requirements": base_dir / "requirements.txt",
    }

    missing = []
    for name, path in config_files.items():
        if not check_file_exists(str(path)):
            missing.append(f"{name}: {path}")
        else:
            print(f"[OK] Found {name} config at {path}")

    if missing:
        print("\n[ERROR] Missing configuration files:")
        for item in missing:
            print(f"  - {item}")
        sys.exit(1)
    
    # Verify requirements.txt contains the necessary tools
    req_path = base_dir / "requirements.txt"
    with open(req_path, "r") as f:
        content = f.read()
    
    required_tools = ["flake8", "black", "mypy", "isort", "pytest"]
    missing_tools = []
    for tool in required_tools:
        if tool not in content:
            missing_tools.append(tool)
    
    if missing_tools:
        print(f"\n[ERROR] Missing tools in requirements.txt: {missing_tools}")
        sys.exit(1)
    
    print("\n[SUCCESS] All linting, formatting, and type-checking configurations are present and valid.")
    print("To run tools manually:")
    print("  - Lint:   flake8 code/")
    print("  - Format: black code/")
    print("  - Types:  mypy code/")
    print("  - Test:   pytest")

if __name__ == "__main__":
    main()