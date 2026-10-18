"""Create the project directory structure per the implementation plan (Task T001).

Creates (idempotently):
  src/, tests/, data/, data/logs/, data/results/, data/reports/,
  specs/001-evaluating-the-effectiveness-of-differen/contracts/, state/projects/

After creation, prints a recursive listing of the created tree as evidence.
"""

from pathlib import Path

from llmxive_toolkit import paths

REQUIRED_DIRS = [
    "src",
    "tests",
    "data",
    "data/logs",
    "data/results",
    "data/reports",
    "specs/001-evaluating-the-effectiveness-of-differen/contracts",
    "state/projects",
]


def create_directories(root: Path = None) -> None:
    """Create all required directories under the project root (idempotent)."""
    root = Path(root) if root is not None else paths.root
    for rel in REQUIRED_DIRS:
        (root / rel).mkdir(parents=True, exist_ok=True)


def main() -> None:
    root = paths.root
    create_directories(root)

    print(f"Project root: {root}")
    print("Created/verified directories:")
    for rel in REQUIRED_DIRS:
        d = root / rel
        assert d.is_dir(), f"FAILED to create {d}"
        print(f"  [OK] {rel}/")

    print("\nDirectory tree (depth 3):")
    for p in sorted(root.rglob("*")):
        depth = len(p.relative_to(root).parts)
        if depth > 3:
            continue
        if p.is_dir():
            print(f"  {p.relative_to(root)}/")


if __name__ == "__main__":
    main()