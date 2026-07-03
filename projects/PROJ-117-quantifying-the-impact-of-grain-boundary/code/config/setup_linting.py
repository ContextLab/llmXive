"""
Script to set up linting and formatting configuration files for the project.
Creates .ruff.toml, .black.toml (or pyproject.toml sections), and updates requirements.
"""
import os
import sys
import json
from pathlib import Path
from config.linting_config import (
    get_ruff_config_file_content,
    get_black_config_file_content,
)

def ensure_pyproject_toml() -> None:
    """Ensure pyproject.toml exists and contains basic project metadata."""
    root = Path(__file__).resolve().parent.parent.parent
    pyproject_path = root / "pyproject.toml"

    if pyproject_path.exists():
        content = pyproject_path.read_text()
        if "[tool.black]" in content:
            print("pyproject.toml already contains Black configuration.")
            return

    # Create or update pyproject.toml
    if not pyproject_path.exists():
        content = "[project]\nname = \"grain-boundary-diffusivity\"\nversion = \"0.1.0\"\n"
    else:
        content = pyproject_path.read_text()

    black_section = get_black_config_file_content()
    # Remove [tool.black] if it exists to avoid duplication
    if "[tool.black]" in content:
        start = content.find("[tool.black]")
        end = content.find("\n[", start + 1)
        if end == -1:
            end = len(content)
        content = content[:start] + content[end:]

    # Append the new black section
    content += "\n" + black_section + "\n"
    pyproject_path.write_text(content)
    print(f"Updated {pyproject_path} with Black configuration.")

def update_requirements() -> None:
    """Add ruff and black to requirements.txt if not present."""
    root = Path(__file__).resolve().parent.parent.parent
    req_path = root / "requirements.txt"

    if not req_path.exists():
        print("requirements.txt not found. Skipping update.")
        return

    content = req_path.read_text()
    lines = content.splitlines()

    required = ["ruff", "black"]
    added = False

    for pkg in required:
        if not any(line.strip().startswith(pkg) for line in lines):
            lines.append(f"{pkg}\n")
            added = True

    if added:
        req_path.write_text("\n".join(lines))
        print("Updated requirements.txt with ruff and black.")
    else:
        print("requirements.txt already contains ruff and black.")

def print_usage_instructions() -> None:
    """Print instructions on how to use the linting tools."""
    print("\n--- Linting and Formatting Instructions ---")
    print("Run the following commands to check code:")
    print("  ruff check .")
    print("  black --check .")
    print("\nTo auto-fix issues:")
    print("  ruff check . --fix")
    print("  black .")
    print("-------------------------------------------\n")

def main() -> None:
    """Main entry point for setup_linting script."""
    print("Setting up linting and formatting tools...")
    ensure_pyproject_toml()
    update_requirements()
    print_usage_instructions()
    print("Setup complete.")

if __name__ == "__main__":
    main()