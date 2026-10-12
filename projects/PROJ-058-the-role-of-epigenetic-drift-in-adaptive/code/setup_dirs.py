"""T001c: Create required project directories.

Creates output/, output/figures/, tests/, tests/unit/, tests/contract/,
logs/, and data/processed/ under the project root. Idempotent: safe to
re-run. Uses paths from llmxive_toolkit so the correct project root is
found regardless of the current working directory.
"""
from pathlib import Path

from llmxive_toolkit import paths

REQUIRED_DIRS = [
    "output",
    "output/figures",
    "tests",
    "tests/unit",
    "tests/contract",
    "logs",
    "data/processed",
]


def create_directories(root: Path) -> list:
    created = []
    for rel in REQUIRED_DIRS:
        target = root / rel
        if not target.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            created.append(rel)
    return created


def main() -> None:
    root = paths.root
    created = create_directories(root)

    # Verify all required directories now exist; fail loudly otherwise.
    missing = [rel for rel in REQUIRED_DIRS if not (root / rel).is_dir()]
    if missing:
        raise RuntimeError(f"Failed to create directories: {missing}")

    if created:
        print("Created directories:")
        for rel in created:
            print(f"  {root / rel}")
    else:
        print("All required directories already exist.")
    print("T001c directory setup complete.")


if __name__ == "__main__":
    main()