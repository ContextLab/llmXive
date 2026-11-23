import os
import sys
import subprocess
from pathlib import Path
from typing import Tuple

def ensure_config_dir() -> Path:
    """
    Ensure the directory where configuration files will be placed exists.
    For this project we store linting/formatting config files inside the
    ``code`` directory to satisfy the repository layout constraints.
    """
    config_dir = Path(__file__).resolve().parent
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir

def create_ruff_config(config_dir: Path) -> Path:
    """
    Create a basic ``.ruff.toml`` configuration file.
    """
    ruff_content = """[format]
indent-style = "space"
line-length = 88

[lint]
select = ["E", "F", "W", "C90"]
ignore = []
exclude = ["__pycache__", ".git", "build", "dist"]
"""
    ruff_path = config_dir / ".ruff.toml"
    ruff_path.write_text(ruff_content.strip() + "\n")
    return ruff_path

def create_black_config(config_dir: Path) -> Path:
    """
    Create a ``pyproject.toml`` file with Black configuration.
    The same file also holds a minimal Ruff configuration section so that
    both tools are configured from a single location.
    """
    pyproject_content = """[tool.black]
line-length = 88
target-version = ["py311"]
skip-string-normalization = false

[tool.ruff]
line-length = 88
select = ["E", "F", "W", "C90"]
ignore = []
exclude = ["__pycache__", ".git", "build", "dist"]
"""
    pyproject_path = config_dir / "pyproject.toml"
    pyproject_path.write_text(pyproject_content.strip() + "\n")
    return pyproject_path

def update_requirements(config_dir: Path) -> Path:
    """
    Ensure that ``ruff`` and ``black`` are listed in ``requirements.txt``.
    If the file does not exist it will be created.
    """
    req_path = config_dir / "requirements.txt"
    if not req_path.exists():
        req_path.touch()
    existing = {line.strip() for line in req_path.read_text().splitlines() if line.strip()}
    needed = {"ruff", "black"}
    combined = sorted(existing.union(needed))
    req_path.write_text("\n".join(combined) + "\n")
    return req_path

def main() -> None:
    """
    Entry point: generate configuration files and update requirements.
    """
    config_dir = ensure_config_dir()
    create_ruff_config(config_dir)
    create_black_config(config_dir)
    update_requirements(config_dir)
    print(f"Linting and formatting configuration files have been created in {config_dir}")

if __name__ == "__main__":
    main()
