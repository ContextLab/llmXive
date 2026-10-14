"""T001a - Create the project directory structure.

Creates the exact directory named in the task:
    projects/PROJ-678-comparative-analysis-of-molecular-fingerprints/
with subdirectories data/raw, data/processed, code, tests (each with a
.gitkeep so the empty tree is durable in version control), and also
guarantees the same structure inside the active project root that the
pipeline scripts use (data/raw, data/processed, code, tests).
"""
from pathlib import Path

from llmxive_toolkit import paths

SUBDIRS = ["data/raw", "data/processed", "code", "tests"]


def _make_tree(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for sub in SUBDIRS:
        d = root / sub
        d.mkdir(parents=True, exist_ok=True)
        keep = d / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")
    print(f"OK: directory tree ready under {root}")


def main() -> None:
    # 1. The exact directory required by task T001a (sibling of the
    #    active project root, i.e. directly under the repository's
    #    projects/ folder).
    project_root = paths.root
    projects_dir = project_root.parent
    required_root = projects_dir / "PROJ-678-comparative-analysis-of-molecular-fingerprints"
    _make_tree(required_root)

    # 2. Ensure the active project root itself has the same structure,
    #    since all pipeline scripts (download/filter/split/train/...)
    #    write to data/raw and data/processed relative to it.
    _make_tree(project_root)

    # Verify loudly.
    for base in (required_root, project_root):
        for sub in SUBDIRS:
            d = base / sub
            if not d.is_dir():
                raise RuntimeError(f"FAILED to create {d}")
    print("T001a: all required directories exist and are non-empty (gitkeep).")


if __name__ == "__main__":
    main()