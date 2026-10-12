"""T001: Create the project directory structure per the implementation plan.

Creates (idempotently) the full directory tree specified in
specs/001-uncovering-correlations-between-processi/plan.md:

    code/            (with data/, models/, utils/, tests/ subpackages)
    data/            (with raw/, processed/, models/, reports/, figures/)
    tests/
    docs/            (with contracts/, research/)

Also ensures Python package markers (__init__.py) exist for importable
packages, and writes a JSON report of the resulting structure to
docs/structure_report.json so the created layout is verifiable on disk.
"""
import json
from pathlib import Path

from llmxive_toolkit import paths

ROOT = paths.root

DIRECTORIES = [
    "code",
    "code/data",
    "code/models",
    "code/utils",
    "code/tests",
    "data",
    "data/raw",
    "data/processed",
    "data/models",
    "data/reports",
    "data/figures",
    "tests",
    "docs",
    "docs/contracts",
    "docs/research",
]

# Packages that must be importable get a package marker if missing.
PACKAGES = ["code", "code/data", "code/models", "code/utils"]

def main() -> None:
    created_dirs = []
    for rel in DIRECTORIES:
        d = ROOT / rel
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created_dirs.append(rel)

    created_markers = []
    for rel in PACKAGES:
        marker = ROOT / rel / "__init__.py"
        if not marker.exists():
            marker.touch()
            created_markers.append(str(marker.relative_to(ROOT)))

    # Keep empty directories tracked in version control.
    for rel in ("data/raw", "data/processed", "tests", "docs/research"):
        keep = ROOT / rel / ".gitkeep"
        if not keep.exists():
            keep.touch()

    report = {
        "task": "T001",
        "root": str(ROOT),
        "directories": DIRECTORIES,
        "directories_created": created_dirs,
        "package_markers_created": created_markers,
        "all_directories_exist": all((ROOT / r).is_dir() for r in DIRECTORIES),
    }
    out = paths.docs("structure_report.json")
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if not report["all_directories_exist"]:
        raise RuntimeError("Failed to create all required directories")

if __name__ == "__main__":
    main()