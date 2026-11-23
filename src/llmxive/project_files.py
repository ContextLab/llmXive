"""Research source locations shared by execution, context, and evidence checks."""

import ast
from collections.abc import Iterator
from pathlib import Path

SOURCE_DIRS = ("code", "src", "scripts")


def requirements_path(project_dir: Path) -> Path:
    """Use the existing manifest; default new projects to code/requirements.txt."""
    code = project_dir / "code/requirements.txt"
    root = project_dir / "requirements.txt"
    return root if root.is_file() and not code.is_file() else code


def requirements_paths(project_dir: Path) -> list[Path]:
    """Every requirements manifest the project has, ``code/`` first.

    :func:`requirements_path` names the ONE file new requirements are written
    to. Installing is a different question: a project that has both files means
    both, and reading one silently drops what the other declares.
    """
    return [path for path in (project_dir / "code/requirements.txt", project_dir / "requirements.txt")
            if path.is_file()]


def source_files(project_dir: Path, suffixes: tuple[str, ...] = (".py",)) -> Iterator[Path]:
    for directory in SOURCE_DIRS:
        for path in sorted((project_dir / directory).rglob("*")):
            if any(part in {".venv", "__pycache__", ".tasks", ".git"} for part in path.parts):
                continue
            if path.is_file() and path.suffix.lower() in suffixes:
                yield path


def is_pytest_module(name: str) -> bool:
    """Whether a file NAME is one pytest collects by default (``test_*.py``, ``*_test.py``)."""
    return name.endswith(".py") and (name.startswith("test_") or name.endswith("_test.py"))


def has_code(name: str, text: str) -> bool:
    """Whether ``text``, as the contents of a file called ``name``, does anything.

    A Python file of comments and a docstring, or a shell script of comments,
    has none. Python that does not parse is counted as code: what it holds is
    unknown, and the caller is deciding whether something would be lost. Any
    other kind of file has content if it is not blank.
    """
    lowered = name.lower()
    if lowered.endswith(".py"):
        try:
            body = ast.parse(text).body
        except (SyntaxError, ValueError):
            return True
        return any(not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant))
                   for node in body)
    if lowered.endswith(".sh"):
        return any(line.strip() and not line.lstrip().startswith("#") for line in text.splitlines())
    return bool(text.strip())
