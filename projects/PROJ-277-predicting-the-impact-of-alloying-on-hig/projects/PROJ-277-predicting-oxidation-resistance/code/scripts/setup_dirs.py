"""Create the project directory tree for PROJ-277.

Creates code/, data/ (raw, processed), tests/ (unit, integration,
contract), and logs/ under the project root, and writes a verifiable
listing of the created tree to logs/directory_tree.txt.
"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(
    __file__).resolve().parents[2]  # .../PROJ-277-predicting-oxidation-resistance

DIRECTORIES = [
    "code",
    "code/data",
    "code/models",
    "code/viz",
    "code/utils",
    "code/scripts",
    "data",
    "data/raw",
    "data/processed",
    "tests",
    "tests/unit",
    "tests/integration",
    "tests/contract",
    "logs",
]

def main() -> int:
    if not PROJECT_ROOT.exists():
        print(f"ERROR: project root missing: {PROJECT_ROOT}", file=sys.stderr)
        return 1

    created = []
    for rel in DIRECTORIES:
        d = PROJECT_ROOT / rel
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created.append(rel)

    # Write evidence listing of the directory tree.
    logs_dir = PROJECT_ROOT / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    listing_path = logs_dir / "directory_tree.txt"
    lines = [f"Project root: {PROJECT_ROOT}", ""]
    for rel in DIRECTORIES:
        d = PROJECT_ROOT / rel
        status = "EXISTS" if d.is_dir() else "MISSING"
        lines.append(f"{rel:30s} [{status}]")
    # Include top-level files for completeness.
    lines.append("")
    lines.append("Top-level entries:")
    for entry in sorted(PROJECT_ROOT.iterdir()):
        kind = "DIR " if entry.is_dir() else "FILE"
        lines.append(f"  {kind} {entry.name}")
    listing_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Created {len(created)} new directories: {created}")
    print(f"Directory tree listing written to {listing_path}")

    # Fail loudly if any required directory is missing.
    missing = [
        rel for rel in DIRECTORIES
        if not (PROJECT_ROOT / rel).is_dir()
    ]
    if missing:
        print(f"ERROR: missing directories: {missing}", file=sys.stderr)
        return 1
    print("All required directories present: OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())