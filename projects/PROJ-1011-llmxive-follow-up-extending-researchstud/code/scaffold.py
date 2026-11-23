"""Scaffolding utility for T001.

Creates the project layout required by the spec:
- code/ (with utils/ and models/ subpackages)
- data/ (with raw/, processed/, results/ subdirectories)
- tests/ (with unit/ and integration/ subdirectories)
- the nested projects/PROJ-1011-llmxive-follow-up-extending-researchstud/
  scaffold expected by tests/test_scaffold_directories.py
- logs/

Idempotent: safe to re-run; existing directories are left untouched.
"""
from llmxive_toolkit import paths

PROJECT_NAME = "PROJ-1011-llmxive-follow-up-extending-researchstud"

TOP_LEVEL_DIRS = [
    "code",
    "code/utils",
    "code/models",
    "data",
    "data/raw",
    "data/processed",
    "data/results",
    "data/experts",
    "tests",
    "tests/unit",
    "tests/integration",
    "logs",
    # Nested scaffold expected by the verification suite
    f"projects/{PROJECT_NAME}",
    f"projects/{PROJECT_NAME}/code",
    f"projects/{PROJECT_NAME}/data",
    f"projects/{PROJECT_NAME}/tests",
]


def create_layout() -> list:
    """Create every scaffold directory; return list of created paths."""
    created = []
    for rel in TOP_LEVEL_DIRS:
        d = paths.path(*rel.split("/"))
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created.append(str(d))
        # .gitkeep so empty dirs survive version control
        keep = d / ".gitkeep"
        if not keep.exists():
            keep.touch()
    return created


def main():
    created = create_layout()
    if created:
        print("Created directories:")
        for c in created:
            print(f"  {c}")
    else:
        print("Project layout already present; nothing to create.")
    print(f"Scaffold complete: {len(TOP_LEVEL_DIRS)} directories verified under {paths.root}")


if __name__ == "__main__":
    main()
