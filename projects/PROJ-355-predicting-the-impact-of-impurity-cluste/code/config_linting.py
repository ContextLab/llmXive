"""
config_linting.py
-----------------
Utility module to configure linting (ruff) and formatting (black) for the project.
It ensures that a ``pyproject.toml`` exists at the project root and that it
contains the required ``[tool.ruff]`` and ``[tool.black]`` sections.  It also
provides a helper to verify that the tools are installed and reachable from
the current environment.
"""
import subprocess
import sys
from pathlib import Path

from config import get_project_root

def ensure_project_root() -> Path:
    """
    Returns the absolute path to the project root directory.
    The function simply forwards to ``config.get_project_root`` which
    implements the logic used throughout the code base.
    """
    return get_project_root()

def _load_pyproject(root: Path) -> str:
    """
    Reads the ``pyproject.toml`` file as a raw string.  If the file does not
    exist it returns an empty string.
    """
    pyproject_path = root / "pyproject.toml"
    if pyproject_path.is_file():
        return pyproject_path.read_text(encoding="utf-8")
    return ""

def _write_pyproject(root: Path, content: str) -> None:
    """
    Writes ``content`` to ``pyproject.toml`` under ``root``.
    Creates the file if it does not exist.
    """
    pyproject_path = root / "pyproject.toml"
    pyproject_path.write_text(content, encoding="utf-8")

def _ensure_section(content: str, header: str, body: str) -> str:
    """
    Ensures that a TOML section identified by ``header`` exists in ``content``.
    If the section is already present, the original content is returned unchanged.
    Otherwise the ``body`` (which should already contain a leading newline) is
    appended to the file.
    """
    if f"[{header}]" in content:
        return content
    # Append a blank line before the new section for readability
    return content.rstrip() + "\n\n" + body.lstrip("\n")

def create_ruff_config(root: Path) -> None:
    """
    Creates or updates the ``[tool.ruff]`` section in ``pyproject.toml``.
    The configuration follows the recommended defaults for this project:
        - line-length: 88
        - select: a set of common error/warning codes
    """
    pyproject = _load_pyproject(root)
    ruff_section = """
    [tool.ruff]
    line-length = 88
    select = [
        "E", "F", "W", "C90", "N", "D", "UP", "YTT", "BLE", "B", "A", "C4",
        "DTZ", "T20", "ISC", "ICN", "G", "PIE", "PYI", "PT", "Q", "RET",
        "SLF", "SIM", "TID", "TCH", "ARG", "FIX", "ERA", "RUF"
    ]
    ignore = []
    """
    updated = _ensure_section(pyproject, "tool.ruff", ruff_section)
    _write_pyproject(root, updated)

def create_black_config(root: Path) -> None:
    """
    Creates or updates the ``[tool.black]`` section in ``pyproject.toml``.
    The configuration mirrors the defaults used by the project:
        - line-length: 88
        - target-version: py311
    """
    pyproject = _load_pyproject(root)
    black_section = """
    [tool.black]
    line-length = 88
    target-version = ["py311"]
    include = '\\.pyi?$'
    exclude = '''
    /(
        \\.eggs
      | \\.git
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
    updated = _ensure_section(pyproject, "tool.black", black_section)
    _write_pyproject(root, updated)

def verify_tools(root: Path) -> bool:
    """
    Checks that the ``ruff`` and ``black`` executables are available in the
    current ``PATH``.  Returns ``True`` only if both commands succeed.
    """
    tools = {"ruff": ["ruff", "--version"], "black": ["black", "--version"]}
    all_ok = True
    for name, cmd in tools.items():
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True,
            )
            print(f"{name} found: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"ERROR: {name} is not installed or not on PATH.", file=sys.stderr)
            all_ok = False
    return all_ok

def main() -> int:
    """
    Entry point used by ``python -m code.config_linting`` or by the
    ``linting_setup`` helper script.  It creates the configuration files
    and reports whether the tools are installed.
    """
    root = ensure_project_root()
    create_ruff_config(root)
    create_black_config(root)

    if verify_tools(root):
        print("Linting and formatting tools are correctly configured.")
        return 0
    else:
        print(
            "One or more tools are missing. Install them with "
            "`pip install ruff black`.",
            file=sys.stderr,
        )
        return 1

if __name__ == "__main__":
    sys.exit(main())
