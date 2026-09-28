"""
Task T003b: Verify pyproject.toml exists and contains required linting configurations.

This script verifies that `pyproject.toml` exists in the project root and explicitly
contains populated [tool.black] and [tool.ruff] sections with the required settings:
- [tool.black]: line-length = 88
- [tool.ruff]: lint.select = ["E", "F"]

It exits with code 0 on success, or 1 on failure (missing file, missing sections, or incorrect values).
"""
import os
import sys
import toml
from pathlib import Path

def main():
    """
    Main entry point for T003b verification.
    
    Returns:
        int: 0 if verification passes, 1 if it fails.
    """
    project_root = Path(__file__).resolve().parent.parent
    pyproject_path = project_root / "pyproject.toml"

    # Check if pyproject.toml exists
    if not pyproject_path.exists():
        print(f"ERROR: {pyproject_path} does not exist.")
        print("Please run T003a first to create the skeleton file.")
        return 1

    try:
        with open(pyproject_path, "r", encoding="utf-8") as f:
            config = toml.load(f)
    except Exception as e:
        print(f"ERROR: Failed to parse {pyproject_path}: {e}")
        return 1

    errors = []

    # Verify [tool.black] section
    if "tool" not in config or "black" not in config["tool"]:
        errors.append("Missing [tool.black] section.")
    else:
        black_config = config["tool"]["black"]
        if "line-length" not in black_config:
            errors.append("[tool.black] is missing 'line-length'.")
        elif black_config["line-length"] != 88:
            errors.append(f"[tool.black] line-length is {black_config['line-length']}, expected 88.")
        else:
            print(f"OK: [tool.black] line-length = {black_config['line-length']}")

    # Verify [tool.ruff] section
    if "tool" not in config or "ruff" not in config["tool"]:
        errors.append("Missing [tool.ruff] section.")
    else:
        ruff_config = config["tool"]["ruff"]
        if "lint" not in ruff_config or "select" not in ruff_config["lint"]:
            errors.append("[tool.ruff] is missing 'lint.select'.")
        else:
            select_list = ruff_config["lint"]["select"]
            if not isinstance(select_list, list):
                errors.append(f"[tool.ruff] lint.select is not a list: {type(select_list)}")
            elif "E" not in select_list or "F" not in select_list:
                errors.append(f"[tool.ruff] lint.select missing 'E' or 'F'. Current: {select_list}")
            else:
                print(f"OK: [tool.ruff] lint.select = {select_list}")

    if errors:
        print("VERIFICATION FAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("VERIFICATION PASSED: pyproject.toml contains required configurations.")
    return 0

if __name__ == "__main__":
    sys.exit(main())