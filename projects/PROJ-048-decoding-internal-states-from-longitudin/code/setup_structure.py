"""T001: Create the project directory structure defined in plan.md.

Creates the exact directory tree:
    code/data, code/analysis, code/utils, code/tests,
    specs/001-decoding-internal-states/contracts

Each directory is created (idempotently) and populated with a .gitkeep
marker file so the structure is visible to git and verifiable on disk.
Running this script prints a listing of the created tree and exits 0.
"""
from pathlib import Path

# Project root is the parent of the directory containing this script.
ROOT = Path(__file__).resolve().parent.parent

DIRECTORIES = [
    "code/data",
    "code/analysis",
    "code/utils",
    "code/tests",
    "specs/001-decoding-internal-states/contracts",
]


def create_structure(root: Path = ROOT) -> None:
    """Create all required directories and .gitkeep marker files."""
    for rel in DIRECTORIES:
        target = root / rel
        target.mkdir(parents=True, exist_ok=True)
        marker = target / ".gitkeep"
        if not marker.exists():
            marker.write_text("", encoding="utf-8")


def main() -> None:
    create_structure()
    print("Project structure created per plan.md:")
    for rel in DIRECTORIES:
        target = ROOT / rel
        assert target.is_dir(), f"missing directory: {target}"
        assert (target / ".gitkeep").exists(), f"missing marker in: {target}"
        print(f"  [ok] {rel}/")


if __name__ == "__main__":
    main()