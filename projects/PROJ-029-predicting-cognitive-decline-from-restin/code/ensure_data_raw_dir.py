"""T002a: Ensure the `data/raw/` directory exists at the repository root.

Creates the directory (idempotent) and writes a small marker file
`data/raw/.gitkeep` plus a listing to `data/raw/README.txt` so the
directory's presence is verifiable in the repository tree.
"""
from llmxive_toolkit import paths

def main() -> int:
    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    keep = raw_dir / ".gitkeep"
    keep.touch(exist_ok=True)
    readme = raw_dir / "README.txt"
    entries = sorted(p.name for p in raw_dir.iterdir())
    readme.write_text(
        "data/raw/ — raw downloaded BIDS data (e.g., OpenNeuro ds000246)\n\n"
        "Current contents:\n" + "\n".join(entries) + "\n",
        encoding="utf-8",
    )
    print(f"data/raw/ ready at {raw_dir} with entries: {entries}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())