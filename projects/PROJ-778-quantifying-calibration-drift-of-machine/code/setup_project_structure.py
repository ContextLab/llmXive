"""T001: Create the project directory structure per the implementation plan.

Creates code/, code/utils/, data/raw/, data/processed/, data/models/,
tests/unit/, tests/integration/ (idempotent) and writes a manifest of the
resulting structure to data/processed/project_structure.txt as evidence.
"""
from pathlib import Path

from llmxive_toolkit import paths

DIRECTORIES = [
    "code",
    "code/utils",
    "data/raw",
    "data/processed",
    "data/models",
    "tests",
    "tests/unit",
    "tests/integration",
]

def create_structure(root: Path) -> None:
    for rel in DIRECTORIES:
        d = root / rel
        d.mkdir(parents=True, exist_ok=True)
        keep = d / ".gitkeep"
        if not any(p for p in d.iterdir() if p.name != ".gitkeep"):
            keep.touch(exist_ok=True)
        elif keep.exists() and any(p for p in d.iterdir() if p.name != ".gitkeep"):
            keep.unlink(missing_ok=True)

def write_manifest(root: Path) -> Path:
    lines = ["# Project structure (T001)", ""]
    for rel in DIRECTORIES:
        d = root / rel
        entries = sorted(
            p.name for p in d.iterdir() if p.name != ".gitkeep"
        )
        lines.append(f"{rel}/ ({len(entries)} entries)")
        for name in entries:
            lines.append(f"  {name}")
    out = paths.data("processed", "project_structure.txt")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out

def main() -> int:
    root = paths.root
    create_structure(root)
    manifest = write_manifest(root)
    print(f"Project structure verified under {root}")
    print(f"Manifest written to {manifest}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())