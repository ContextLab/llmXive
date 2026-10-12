"""Create the code/data/ directory structure (raw/, processed/) for T006.

Creates:
    code/data/raw/        - raw (downloaded/generated) data files
    code/data/processed/  - cleaned, standardized datasets

Each directory is populated with a .gitkeep file so the structure is
preserved in version control and its existence is verifiable on disk.
"""

from pathlib import Path

from llmxive_toolkit import paths

DIRECTORIES = [
    ("raw", "Raw (downloaded or generated) input data files."),
    ("processed", "Cleaned, standardized, and feature-engineered datasets."),
]


def create_data_directories() -> None:
    """Create code/data/raw/ and code/data/processed/ with .gitkeep files."""
    for name, description in DIRECTORIES:
        target = paths.code("data", name)
        target.mkdir(parents=True, exist_ok=True)
        gitkeep = target / ".gitkeep"
        gitkeep.write_text(
            f"# {description}\n", encoding="utf-8"
        )
        print(f"Created/verified: {target} (with .gitkeep)")


if __name__ == "__main__":
    create_data_directories()
    # Fail loudly if anything is missing afterwards.
    for name, _ in DIRECTORIES:
        d = paths.code("data", name)
        if not d.is_dir() or not (d / ".gitkeep").is_file():
            raise RuntimeError(f"Directory verification failed for {d}")
    print("code/data/ directory structure is complete.")