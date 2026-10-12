"""T001a: Create the standard project directory structure.

Creates data/raw, data/processed, results/models, results/reports,
results/plots, code, tests (and tests/unit, tests/integration), then
writes a listing artifact to results/reports/structure_listing.txt as
evidence that the hierarchy exists.
"""
from pathlib import Path

from llmxive_toolkit import paths

DIRECTORIES = [
    "data/raw",
    "data/processed",
    "results/models",
    "results/reports",
    "results/plots",
    "code",
    "tests",
    "tests/unit",
    "tests/integration",
]

def main() -> int:
    root = paths.root
    created = []
    for d in DIRECTORIES:
        p = root / d
        p.mkdir(parents=True, exist_ok=True)
        created.append(d)
        assert p.is_dir(), f"Failed to create {p}"

    # Evidence artifact: listing of the created hierarchy.
    lines = ["T001a project directory structure listing", ""]
    for d in DIRECTORIES:
        p = root / d
        lines.append(f"{'[DIR] ' if p.is_dir() else '[MISSING] '}{d}")

    listing_path = paths.results("reports", "structure_listing.txt")
    listing_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\n".join(lines))
    print(f"\nListing written to {listing_path}")
    print(f"Created {len(created)} directories: {', '.join(created)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())