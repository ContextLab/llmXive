"""
Setup script for linting and formatting tools (Ruff, Black, Flake8).
This script creates configuration files if they do not already exist.
"""
import os
import sys
from pathlib import Path
import tomllib
import configparser
import argparse


def check_file_exists(path: Path) -> bool:
    return path.exists()


def validate_ruff_config(path: Path) -> bool:
    if not check_file_exists(path):
        return False
    # Ruff config is typically in pyproject.toml or .ruff.toml
    if path.suffix == ".toml":
        try:
            with open(path, "rb") as f:
                data = tomllib.load(f)
            # Basic validation: check for [tool.ruff] or [lint] section
            if "tool" in data and "ruff" in data["tool"]:
                return True
            if "lint" in data:
                return True
        except Exception:
            return False
    return True


def validate_pyproject_black(path: Path) -> bool:
    if not check_file_exists(path):
        return False
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
        return "tool" in data and "black" in data["tool"]
    except Exception:
        return False


def validate_flake8(path: Path) -> bool:
    return check_file_exists(path)


def create_ruff_config(root: Path) -> None:
    path = root / ".ruff.toml"
    if path.exists():
        print(f"Skipping creation of {path}: already exists.")
        return

    content = """[lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
]
ignore = [
    "E501", # line too long (handled by black)
    "B008", # do not perform function calls in argument defaults
]

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created {path}")


def create_black_config(root: Path) -> None:
    # Black config is usually in pyproject.toml
    pyproject_path = root / "pyproject.toml"
    if pyproject_path.exists():
        try:
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
            if "tool" in data and "black" in data["tool"]:
                print(f"Skipping creation of Black config in {pyproject_path}: already exists.")
                return
        except Exception:
            pass

    # If pyproject.toml doesn't exist or doesn't have black config, we might append it
    # For simplicity, we'll just ensure the section exists in the file
    with open(pyproject_path, "r+", encoding="utf-8") as f:
        content = f.read()
        if "[tool.black]" not in content:
            f.write("\n[tool.black]\n")
            f.write('line-length = 88\n')
            f.write("target-version = ['py39', 'py310', 'py311']\n")
            f.write("include = '\\\\.pyi?$'\n")
            f.write("""exclude = '''
/(
    \\.git
  | \\.hg
  | \\.mypy_cache
  | \\.tox
  | \\.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''\n""")
    print(f"Updated {pyproject_path} with Black config.")


def create_flake8_config(root: Path) -> None:
    path = root / ".flake8"
    if path.exists():
        print(f"Skipping creation of {path}: already exists.")
        return

    content = """[flake8]
max-line-length = 88
exclude = .git,__pycache__,build,dist
ignore = E501,W503
per-file-ignores =
    # Allow unused imports in __init__.py
    */__init__.py:F401
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created {path}")


def install_linting_tools() -> None:
    """
    Attempt to install linting tools if they are not present.
    This is a best-effort check; actual installation depends on environment.
    """
    import subprocess

    tools = [
        ("ruff", "ruff"),
        ("black", "black"),
        ("flake8", "flake8"),
    ]

    for name, cmd in tools:
        try:
            subprocess.run([cmd, "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"{name} is already installed.")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"{name} not found. Attempting to install...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", name], check=True)
                print(f"Installed {name}.")
            except subprocess.CalledProcessError:
                print(f"Failed to install {name}. Please install manually.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Setup linting and formatting tools.")
    parser.add_argument("--root", type=Path, default=Path("."), help="Project root directory")
    args = parser.parse_args()

    root = args.root.resolve()
    print(f"Setting up linting tools in {root}")

    # Create configurations
    create_ruff_config(root)
    create_black_config(root)
    create_flake8_config(root)

    # Attempt to install tools
    install_linting_tools()

    print("Linting setup complete.")


if __name__ == "__main__":
    main()