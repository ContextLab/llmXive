"""Create the project directory structure per the implementation plan (T001).

Creates the required top-level folders (code/, tests/, data/, results/,
specs/) plus the subdirectories defined in plan.md (data/raw, data/processed,
data/logs, results/figures) and drops .gitkeep markers so the empty
directories are preserved in version control.
"""

from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

REQUIRED_DIRS = [
    "code",
    "code/tests",
    "tests",
    "data",
    "data/raw",
    "data/processed",
    "data/logs",
    "results",
    "results/figures",
    "specs",
    "specs/001-sentiment-revenue-lag-analysis",
    "specs/001-statistical-analysis-of-publicly-availab/contracts",
]


def create_structure() -> list:
    """Create all required directories and .gitkeep markers.

    Returns the list of directories that were created (empty if all
    already existed).
    """
    created = []
    for rel in REQUIRED_DIRS:
        d = paths.path(rel)
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created.append(rel)
            log.info("Created directory: %s", d)
        keep = d / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")
    return created


def main() -> None:
    created = create_structure()
    if created:
        print("Created directories:")
        for rel in created:
            print(f"  {rel}")
    else:
        print("All required directories already exist.")
    print("Project structure is complete:")
    for rel in REQUIRED_DIRS:
        print(f"  {paths.path(rel)}")


if __name__ == "__main__":
    main()
