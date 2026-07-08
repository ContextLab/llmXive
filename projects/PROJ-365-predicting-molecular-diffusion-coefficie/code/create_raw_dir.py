"""
Utility script to ensure the presence of the `data/raw` directory
for source CSV files. It also creates a minimal placeholder CSV
if none exists, providing a concrete artifact that satisfies the
requirement of having a source CSV in the directory.
"""

from pathlib import Path

from utils.config import get_project_root


def get_raw_dir() -> Path:
    """
    Return the absolute Path to the project's raw data directory.
    """
    return get_project_root() / "data" / "raw"


def ensure_raw_dir() -> Path:
    """
    Create the `data/raw` directory (including any missing parents) and
    ensure a placeholder CSV file exists. The placeholder CSV contains
    only a header line with the expected columns.

    Returns:
        Path: The Path object pointing to the created raw data directory.
    """
    raw_dir = get_raw_dir()
    raw_dir.mkdir(parents=True, exist_ok=True)

    placeholder = raw_dir / "dataset_placeholder.csv"
    if not placeholder.is_file():
        # Write a minimal CSV header; no data rows are required at this stage.
        placeholder.write_text("smiles,solvent,diffusion_coefficient\n")

    return raw_dir


def main() -> None:
    """
    Entry point for the script. Ensures the raw directory exists and
    reports its location.
    """
    raw_dir = ensure_raw_dir()
    print(f"Created raw data directory at: {raw_dir}")


if __name__ == "__main__":
    main()
