"""Create the project directory structure for T001.

Creates the directories required by the project plan (code/, data/,
results/, tests/, contracts/, docs/ and the pipeline sub-packages) if
they do not already exist. README.md and .gitignore are provided as
separate artifacts in the repository; this script only ensures the
directory skeleton exists on disk.
"""
from pathlib import Path

from llmxive_toolkit import paths

DIRECTORIES = [
    "code",
    "code/pipeline",
    "code/feature_engineering",
    "code/models",
    "code/tests",
    "data",
    "data/raw",
    "data/processed",
    "results",
    "tests",
    "tests/contract",
    "tests/integration",
    "contracts",
    "docs",
]

def create_project_structure(root: Path) -> list:
    """Create all required directories under root.

    Args:
        root: Project root directory.

    Returns:
        List of directories that were newly created.
    """
    created = []
    for d in DIRECTORIES:
        target = root / d
        if not target.exists():
            target.mkdir(parents=True, exist_ok=True)
            created.append(d)
    return created

def main() -> int:
    root = paths.root
    created = create_project_structure(root)
    if created:
        print(f"Created {len(created)} directories:")
        for d in created:
            print(f"  {d}")
    else:
        print("All required directories already exist.")
    # Verify every required directory exists.
    missing = [d for d in DIRECTORIES if not (root / d).is_dir()]
    if missing:
        raise RuntimeError(f"Missing directories after setup: {missing}")
    print("Project structure verified.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
