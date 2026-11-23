"""Create the data directory structure required by the pipeline.

Task T001.3: Create data/raw/, data/descriptors/, data/processed/
subdirectories. These directories hold the downloaded CIFs, derived
descriptor CSVs, and the train/val/test splits respectively.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIRECTORIES = [
    "data/raw",
    "data/descriptors",
    "data/processed",
]


def create_data_directories(directories=None, base=PROJECT_ROOT):
    """Create each data subdirectory (and parents) under the project root.

    Returns the list of created directory paths.
    """
    created = []
    dirs = directories if directories is not None else DATA_DIRECTORIES
    for d in dirs:
        target = (base / d) if isinstance(d, str) else Path(d)
        target.mkdir(parents=True, exist_ok=True)
        # Keep empty directories present in version control.
        gitkeep = target / ".gitkeep"
        if not any(p.name != ".gitkeep" for p in target.iterdir()):
            gitkeep.touch()
        created.append(target)
    return created


def main():
    created = create_data_directories()
    for path in created:
        print(f"created: {path}")
    # Verify all required directories exist.
    missing = [p for p in created if not p.is_dir()]
    if missing:
        print(f"FATAL: missing directories: {missing}", file=sys.stderr)
        sys.exit(1)
    print("All data directories ready.")


if __name__ == "__main__":
    main()