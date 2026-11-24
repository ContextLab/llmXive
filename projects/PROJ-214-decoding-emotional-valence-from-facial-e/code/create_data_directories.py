"""T001b: Create data/raw, data/processed, data/models, data/logs directories.

Also writes a directory listing to data/logs/directory_structure.txt as
persistent evidence that the required structure exists (Constitution
Principle V traceability).
"""
from pathlib import Path

from llmxive_toolkit import paths

REQUIRED_DIRS = ["raw", "processed", "models", "logs"]


def main() -> None:
    created = []
    for sub in REQUIRED_DIRS:
        d = paths.data(sub)
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created.append(sub)
    # Drop .gitkeep so the empty directories are tracked by git.
    for sub in REQUIRED_DIRS:
        keep = paths.data(sub) / ".gitkeep"
        if not any(p for p in paths.data(sub).iterdir()):
            keep.touch()

    # Evidence: write a listing of the data/ tree.
    lines = ["data/ directory structure (T001b evidence):"]
    for sub in REQUIRED_DIRS:
        d = paths.data(sub)
        assert d.is_dir(), f"missing directory: {d}"
        entries = sorted(p.name for p in d.iterdir())
        lines.append(f"  {d.relative_to(paths.root)}/ -> exists, entries: {entries}")
    lines.append(f"newly created in this run: {created}")
    out = paths.data("logs", "directory_structure.txt")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nevidence written to: {out}")


if __name__ == "__main__":
    main()