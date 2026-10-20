"""Create the data/processed/ directory (task T002b).

Ensures ``data/processed/`` exists at the repository root and leaves a
small README marker so the directory is tracked by version control.
Exits non-zero if the directory cannot be created.
"""
import sys
from pathlib import Path

from llmxive_toolkit import paths

def main() -> int:
    processed_dir = paths.data("processed")
    try:
        processed_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"ERROR: could not create data/processed/: {exc}", file=sys.stderr)
        return 1

    marker = processed_dir / ".gitkeep"
    if not marker.exists():
        marker.write_text("", encoding="utf-8")

    if not processed_dir.is_dir():
        print("ERROR: data/processed/ still missing after creation.", file=sys.stderr)
        return 1

    print(f"data/processed/ ready at {processed_dir}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
