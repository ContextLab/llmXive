"""Research source locations shared by execution, context, and evidence checks."""

from collections.abc import Iterator
from pathlib import Path

SOURCE_DIRS = ("code", "src", "scripts")


def requirements_path(project_dir: Path) -> Path:
    """Use the existing manifest; default new projects to code/requirements.txt."""
    code = project_dir / "code/requirements.txt"
    root = project_dir / "requirements.txt"
    return root if root.is_file() and not code.is_file() else code


def source_files(project_dir: Path, suffixes: tuple[str, ...] = (".py",)) -> Iterator[Path]:
    for directory in SOURCE_DIRS:
        for path in sorted((project_dir / directory).rglob("*")):
            if any(part in {".venv", "__pycache__", ".tasks", ".git"} for part in path.parts):
                continue
            if path.is_file() and path.suffix.lower() in suffixes:
                yield path
