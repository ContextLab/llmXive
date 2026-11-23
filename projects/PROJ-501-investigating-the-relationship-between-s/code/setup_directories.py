"""Create the required project directory structure for data and contracts.

Directories created (relative to the project root, regardless of the
current working directory):
- data/raw/
- data/processed/
- data/results/
- data/logs/
- contracts/

Each directory is created if missing and kept non-empty (a `.gitkeep`
marker is added to otherwise-empty directories) so the structure is
verifiable in version control. A human-readable listing of the created
structure is written to data/logs/directory_structure.txt as evidence.
"""

import sys
import traceback
from pathlib import Path

from llmxive_toolkit import paths

# Canonical directory list for this project (see tasks.md T002).
REQUIRED_DIRECTORIES = [
    "data/raw",
    "data/processed",
    "data/results",
    "data/logs",
    "contracts",
]


def _resolve(rel: str) -> Path:
    """Resolve a project-relative directory path via the toolkit."""
    parts = Path(rel).parts
    if not parts:
        raise ValueError("Empty relative path")
    top = parts[0]
    rest = parts[1:]
    return paths.path(top, *rest) if hasattr(paths, "path") else Path(paths.root) / rel


def create_directories() -> bool:
    """Create the required project directory structure.

    Returns:
        bool: True if all required directories exist and are non-empty,
        False otherwise.
    """
    created: list[Path] = []
    all_ok = True
    for rel in REQUIRED_DIRECTORIES:
        directory = _resolve(rel)
        directory.mkdir(parents=True, exist_ok=True)
        # Keep the directory non-empty so its existence is verifiable.
        if not any(directory.iterdir()):
            (directory / ".gitkeep").touch()
        created.append(directory)
        if not directory.is_dir() or not any(directory.iterdir()):
            all_ok = False

    # Write an evidence listing of the created structure.
    try:
        listing_path = paths.data("logs", "directory_structure.txt")
        lines = []
        root = Path(paths.root)
        for directory in created:
            lines.append(f"{directory.relative_to(root)}/")
            for child in sorted(directory.iterdir()):
                lines.append(f"  {child.name}")
        listing_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except Exception:  # evidence listing must never break directory creation
        traceback.print_exc()

    for directory in created:
        print(f"[setup_directories] OK: {directory}")
    return all_ok


def main() -> None:
    success = create_directories()
    if not success:
        print("[setup_directories] FAILED to create all directories", file=sys.stderr)
        sys.exit(1)
    print("[setup_directories] All required directories exist and are non-empty.")


if __name__ == "__main__":
    main()