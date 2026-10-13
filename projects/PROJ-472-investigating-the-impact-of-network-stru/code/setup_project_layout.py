"""T001: create the project directory layout.

Creates code/, tests/ and the data/ sub-tree (raw/, processed/, results/,
figures/) with .gitkeep markers so the empty directories are tracked,
and initialises data/raw/.checksums.json if absent.
"""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DIRECTORIES = [
    PROJECT_ROOT / "code",
    PROJECT_ROOT / "tests",
    PROJECT_ROOT / "data" / "raw",
    PROJECT_ROOT / "data" / "processed",
    PROJECT_ROOT / "data" / "results",
    PROJECT_ROOT / "data" / "figures",
]

def main() -> None:
    for d in DIRECTORIES:
        d.mkdir(parents=True, exist_ok=True)
        keep = d / ".gitkeep"
        if not any(p for p in d.iterdir() if p.name != ".gitkeep"):
            keep.touch()
        print(f"ready: {d.relative_to(PROJECT_ROOT)}")

    checksums = PROJECT_ROOT / "data" / "raw" / ".checksums.json"
    if not checksums.exists():
        checksums.write_text(json.dumps({}, indent=2) + "\n")
        print("initialised: data/raw/.checksums.json")

if __name__ == "__main__":
    main()