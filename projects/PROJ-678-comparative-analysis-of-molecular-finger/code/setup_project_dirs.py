"""T001a: Create the project directory structure.

Creates data/raw, data/processed, code, and tests directories (with
.gitkeep markers for the data directories) under the project root.
"""
from pathlib import Path

from llmxive_toolkit import paths


def main() -> None:
    root = paths.root
    dirs = [
        root / "data" / "raw",
        root / "data" / "processed",
        root / "code",
        root / "tests",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"created: {d}")

    # .gitkeep markers so empty data dirs are tracked
    for d in (root / "data" / "raw", root / "data" / "processed"):
        keep = d / ".gitkeep"
        if not keep.exists():
            keep.touch()
        print(f"marker: {keep}")

    # Sanity check per task verification
    for d in dirs:
        assert d.is_dir(), f"missing directory: {d}"
    assert (root / "data" / "raw" / ".gitkeep").exists()
    assert (root / "data" / "processed" / ".gitkeep").exists()
    print("T001a directory structure verified OK")


if __name__ == "__main__":
    main()