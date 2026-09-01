"""
Setup script to install and configure linting (ruff) and formatting (black) tools.
This script updates requirements.txt and creates necessary config files if missing.
"""
import os
import sys
from pathlib import Path

def ensure_ruff_config():
    """Create .ruff.toml if it doesn't exist."""
    root = Path(__file__).parent.parent
    config_path = root / ".ruff.toml"
    if not config_path.exists():
        config_path.write_text(
            "[lint]\n"
            "select = [\"E\", \"W\", \"F\", \"I\", \"C\", \"B\"]\n"
            "ignore = [\"E501\", \"B008\"]\n"
            "exclude = [\"data/raw\", \"data/processed\", \"__pycache__\"]\n"
            "\n"
            "[lint.isort]\n"
            "known-first-party = [\"code\"]\n"
        )
        print(f"Created {config_path}")
    else:
        print(f"Config already exists: {config_path}")

def ensure_black_config():
    """Ensure pyproject.toml has black config."""
    root = Path(__file__).parent.parent
    pyproject_path = root / "pyproject.toml"
    
    if not pyproject_path.exists():
        pyproject_path.write_text(
            "[tool.black]\n"
            "line-length = 88\n"
            "target-version = ['py311']\n"
        )
        print(f"Created {pyproject_path}")
        return

    content = pyproject_path.read_text()
    if "[tool.black]" not in content:
        with open(pyproject_path, "a") as f:
            f.write("\n[tool.black]\nline-length = 88\ntarget-version = ['py311']\n")
        print(f"Updated {pyproject_path} with black config")
    else:
        print(f"Black config already exists in {pyproject_path}")

def update_requirements():
    """Append linting dependencies to requirements.txt if missing."""
    root = Path(__file__).parent.parent
    req_path = root / "requirements.txt"
    
    if not req_path.exists():
        req_path.write_text("ruff\nblack\n")
        print(f"Created {req_path}")
        return

    with open(req_path, "r") as f:
        lines = f.readlines()

    existing = {line.strip().split("==")[0].split(">")[0].split("<")[0].lower() for line in lines}
    
    needs_update = False
    if "ruff" not in existing:
        lines.append("ruff\n")
        needs_update = True
    if "black" not in existing:
        lines.append("black\n")
        needs_update = True

    if needs_update:
        with open(req_path, "w") as f:
            f.writelines(lines)
        print(f"Updated {req_path}")
    else:
        print(f"Dependencies already present in {req_path}")

def main():
    print("Configuring linting and formatting tools...")
    ensure_ruff_config()
    ensure_black_config()
    update_requirements()
    print("Configuration complete. Run 'pip install -r requirements.txt' to install tools.")

if __name__ == "__main__":
    main()