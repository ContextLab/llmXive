"""
Script to establish the required project layout and capture a filesystem
snapshot for verification (T001).

It creates all directories listed in ``REQUIRED_DIRS`` relative to the
repository root and writes a tree‑like listing (up to depth 3) to
``logs/structure.txt``.  If the external ``tree`` command is unavailable,
a pure‑Python fallback walks the directory tree and produces a similar
output.
"""

import os
import subprocess
from pathlib import Path
from typing import List

# ----------------------------------------------------------------------
# Configuration – list of directories that must exist for the project.
# ----------------------------------------------------------------------
REQUIRED_DIRS = [
    Path("src/data"),
    Path("src/analysis"),
    Path("src/utils"),
    Path("src/validation"),
    Path("tests/unit"),
    Path("tests/integration"),
    Path("tests/fixtures"),
    Path("data/raw"),
    Path("data/processed"),
    Path("data/results"),
    Path("output/figures"),
    Path("output/temporal_profiles"),
    Path("logs"),
]

# ----------------------------------------------------------------------
# Helper: create all required directories (including parents).
# ----------------------------------------------------------------------
def _create_directories(root: Path) -> None:
    """Create every directory in ``REQUIRED_DIRS`` under ``root``."""
    for rel_dir in REQUIRED_DIRS:
        dir_path = root / rel_dir
        dir_path.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# Helper: generate a tree‑like snapshot using the system ``tree`` command.
# ----------------------------------------------------------------------
def _run_tree(root: Path, max_depth: int = 3) -> str:
    """Run ``tree -a -L <max_depth>``; fallback to Python if unavailable."""
    try:
        completed = subprocess.run(
            ["tree", "-a", f"-L{max_depth}", str(root)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return completed.stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        # ``tree`` not installed or failed – use Python fallback.
        return _python_tree_fallback(root, max_depth)

# ----------------------------------------------------------------------
# Python fallback that mimics ``tree`` output (directories only).
# ----------------------------------------------------------------------
def _python_tree_fallback(root: Path, max_depth: int = 3) -> str:
    """
    Walk ``root`` up to ``max_depth`` levels and return a string where each
    line is a relative path (directories end with a slash).  The format is
    deliberately simple – it only needs to contain one line per directory
    for the verification step.
    """
    lines: List[str] = []

    def _walk(current: Path, current_depth: int) -> None:
        if current_depth > max_depth:
            return
        rel = current.relative_to(root)
        # Root itself is printed as '.' by ``tree`` – we mimic that.
        prefix = "." if rel == Path("") else str(rel)
        # Ensure directories end with a slash.
        lines.append(f"{prefix}/")
        for child in sorted(current.iterdir()):
            if child.is_dir():
                _walk(child, current_depth + 1)

    _walk(root, 0)
    return "\n".join(lines) + "\n"

# ----------------------------------------------------------------------
# Main entry point.
# ----------------------------------------------------------------------
def main() -> None:
    """
    Create the directory layout and write ``logs/structure.txt``.
    The function exits with status 0 on success; any unexpected exception
    will cause a non‑zero exit code (allowing the runner to surface the
    failure).
    """
    project_root = Path.cwd()
    # 1. Create required directories.
    _create_directories(project_root)

    # 2. Capture the filesystem snapshot.
    snapshot = _run_tree(project_root, max_depth=3)

    # 3. Write the snapshot to the expected location.
    logs_dir = project_root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    output_file = logs_dir / "structure.txt"
    output_file.write_text(snapshot, encoding="utf-8")

if __name__ == "__main__":
    main()
