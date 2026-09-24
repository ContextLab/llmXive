import os
import sys
from pathlib import Path
import subprocess

"""
Utilities to set up linting (ruff) and formatting (black) for the project.

The script creates configuration files at the repository root:
  - .ruff.toml
  - pyproject.toml (containing Black configuration)

It also ensures that the required packages (ruff, black) are listed in
``requirements.txt``.  The script can be executed directly:

    python code/setup_linting_formatting.py

It is safe to run multiple times; existing configuration files will be
overwritten with the canonical content and missing entries will be added
to ``requirements.txt``.
"""

def ensure_config_dir() -> Path:
    """
    Ensure that the current working directory (project root) exists.
    Returns the Path object representing the root directory.
    """
    root = Path.cwd()
    root.mkdir(parents=True, exist_ok=True)
    return root

def create_ruff_config(root: Path) -> None:
    """
    Write a standard ``.ruff.toml`` configuration file to the project root.
    If the file already exists it will be overwritten with the canonical
    configuration.
    """
    ruff_config = """[tool.ruff]
target-version = "py311"
line-length = 88
select = ["E", "F", "W", "C90"]
fix = true
"""
    config_path = root / ".ruff.toml"
    config_path.write_text(ruff_config, encoding="utf-8")
    print(f"Created ruff config at {config_path}")

def create_black_config(root: Path) -> None:
    """
    Write a ``pyproject.toml`` containing Black configuration.
    If a ``pyproject.toml`` already exists we preserve any existing
    content that does not belong to the ``[tool.black]`` table.
    """
    black_section = """[tool.black]
line-length = 88
target-version = ["py311"]
include = '\\.pyi?$'
exclude = '''
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
'''
"""

    pyproject_path = root / "pyproject.toml"

    if pyproject_path.exists():
        # Preserve non‑black sections
        existing = pyproject_path.read_text(encoding="utf-8")
        lines = existing.splitlines()
        # Remove any existing [tool.black] block
        filtered = []
        inside_black = False
        for line in lines:
            if line.strip().startswith("[tool.black]"):
                inside_black = True
                continue
            if inside_black and line.startswith("["):
                inside_black = False
            if not inside_black:
                filtered.append(line)
        new_content = "\n".join(filtered).strip()
        if new_content:
            new_content += "\n\n"
        new_content += black_section
    else:
        new_content = black_section

    pyproject_path.write_text(new_content, encoding="utf-8")
    print(f"Created/updated Black config at {pyproject_path}")

def update_requirements(root: Path) -> None:
    """
    Ensure that ``requirements.txt`` exists and contains entries for
    ``ruff`` and ``black``.  Existing entries are left untouched.
    """
    req_path = root / "requirements.txt"
    required = {"ruff", "black"}

    if req_path.exists():
        existing = {line.strip() for line in req_path.read_text(encoding="utf-8").splitlines() if line.strip()}
    else:
        existing = set()

    missing = required - existing
    if missing:
        with req_path.open("a", encoding="utf-8") as f:
            for pkg in sorted(missing):
                f.write(f"{pkg}\n")
        print(f"Added missing packages to {req_path}: {', '.join(sorted(missing))}")
    else:
        print(f"All required packages already present in {req_path}")

def main() -> None:
    """
    Entry point for the script.  It creates the configuration files and
    updates ``requirements.txt``.
    """
    root = ensure_config_dir()
    create_ruff_config(root)
    create_black_config(root)
    update_requirements(root)
    print("Linting and formatting tools configured successfully.")

if __name__ == "__main__":
    # When executed as a script we explicitly set the working directory to the
    # repository root (the directory containing this file's parent ``code`` folder).
    # This makes the script robust when called from any location.
    repo_root = Path(__file__).resolve().parent.parent
    os.chdir(repo_root)
    main()