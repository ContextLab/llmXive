"""Project scaffolding for the VAERS statistical analysis pipeline (T001).

Creates the required directory layout (including ``data/processed/``,
which a previous run omitted) and writes the filesystem evidence
artifact ``logs/structure.txt`` containing the output of
``tree -a -L 3`` (falling back to ``find . -maxdepth 3 -type d`` when
the ``tree`` binary is unavailable).

Usage:
    python code/create_structure.py
"""

import subprocess
from pathlib import Path

from llmxive_toolkit import paths

REQUIRED_DIRS = [
    "src",
    "src/data",
    "src/analysis",
    "src/utils",
    "src/validation",
    "tests",
    "tests/unit",
    "tests/integration",
    "data",
    "data/raw",
    "data/processed",
    "data/results",
    "output",
    "output/figures",
    "output/temporal_profiles",
    "logs",
]


def create_directories(root: Path | None = None) -> list[Path]:
    """Create all required project directories (idempotent).

    Returns the list of directories that were newly created.
    """
    base = Path(root) if root else paths.root
    created: list[Path] = []
    for rel in REQUIRED_DIRS:
        d = base / rel
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created.append(d)
    return created


def write_structure_snapshot(root: Path | None = None) -> Path:
    """Capture a three-level directory listing into logs/structure.txt.

    Prefers the system ``tree -a -L 3`` command; if it is not
    installed, falls back to ``find . -maxdepth 3 -type d``.
    """
    base = Path(root) if root else paths.root
    logs_dir = base / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    out_file = logs_dir / "structure.txt"

    try:
        result = subprocess.run(
            ["tree", "-a", "-L", "3"],
            cwd=str(base),
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
        )
        listing = result.stdout
    except (FileNotFoundError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired):
        result = subprocess.run(
            ["find", ".", "-maxdepth", "3", "-type", "d"],
            cwd=str(base),
            capture_output=True,
            text=True,
            check=True,
            timeout=60,
        )
        listing = result.stdout

    if not listing.strip():
        raise RuntimeError(
            "Failed to capture directory structure: both 'tree' and "
            "'find' produced empty output."
        )

    out_file.write_text(listing, encoding="utf-8")
    return out_file


def main() -> None:
    created = create_directories()
    if created:
        print(f"Created {len(created)} directories:")
        for d in created:
            print(f"  {d.relative_to(paths.root)}")
    else:
        print("All required directories already exist.")

    out_file = write_structure_snapshot()
    size = out_file.stat().st_size
    print(f"Wrote {out_file} ({size} bytes)")
    if size == 0:
        raise RuntimeError("logs/structure.txt is empty")


if __name__ == "__main__":
    main()