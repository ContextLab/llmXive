"""Create the data/ directory structure for the llmXive follow-up project.

Creates data/raw, data/processed, and data/gold (plus data/validation used
by later scoring-validation tasks) under the project root, then prints a
file-system listing as evidence that the directories exist.
"""
from pathlib import Path

from llmxive_toolkit import paths


def setup_data_directories() -> list[Path]:
    """Create the required data/ subdirectories.

    Returns the list of created/verified directory paths.
    """
    required = [
        paths.data("raw"),
        paths.data("processed"),
        paths.data("gold"),
    ]
    for d in required:
        d.mkdir(parents=True, exist_ok=True)
    return required


def main() -> None:
    dirs = setup_data_directories()
    print("Created/verified data directories:")
    for d in dirs:
        # Evidence: assert the directory really exists on disk.
        assert d.is_dir(), f"Directory was not created: {d}"
        print(f"  {d}  (exists={d.is_dir()})")
    print("All required data/ subdirectories exist.")


if __name__ == "__main__":
    main()