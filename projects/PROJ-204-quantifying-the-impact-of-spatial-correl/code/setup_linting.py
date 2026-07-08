import os
from pathlib import Path

__all__ = ["create_config_files"]

def create_config_files(project_root: Path = Path(".")) -> None:
    """
    Create basic linting and formatting configuration files.

    This function generates a ``.ruff.toml`` for ruff, a ``.flake8`` for
    flake8, and adds a ``[tool.black]`` section to ``pyproject.toml`` if it
    does not already exist.

    Parameters
    ----------
    project_root: Path, optional
        Root directory of the repository (default current directory).
    """
    ruff_cfg = project_root / ".ruff.toml"
    flake8_cfg = project_root / ".flake8"
    pyproject_cfg = project_root / "pyproject.toml"

    if not ruff_cfg.exists():
        ruff_cfg.write_text("[tool.ruff]\nselect = [\"E\", \"F\", \"W\", \"C90\"]\n")
    if not flake8_cfg.exists():
        flake8_cfg.write_text("[flake8]\nmax-line-length = 88\n")
    if pyproject_cfg.exists():
        content = pyproject_cfg.read_text()
        if "[tool.black]" not in content:
            with pyproject_cfg.open("a") as f:
                f.write("\n[tool.black]\nline-length = 88\n")
    else:
        pyproject_cfg.write_text("[tool.black]\nline-length = 88\n")
    print("Linting and formatting configuration files created/updated.")
