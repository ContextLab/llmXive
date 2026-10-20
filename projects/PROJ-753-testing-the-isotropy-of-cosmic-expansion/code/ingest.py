"""Ingestion script for Pantheon+ dataset.

This minimal implementation satisfies the project scaffolding requirements.
It verifies the presence of the raw data file and creates a placeholder
``residuals.csv`` file in ``data/processed`` when run without ``--verify-only``.
Full scientific functionality will be added in later tasks.
"""
import argparse
from pathlib import Path

from utils import get_logger

def verify_raw_file(raw_path: Path) -> None:
    """Raise an error if the expected raw data file does not exist."""
    if not raw_path.is_file():
        raise FileNotFoundError(f"Raw data file not found: {raw_path}")
    logger = get_logger(__name__)
    logger.info("Raw data file verified: %s", raw_path)

def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest Pantheon+ data")
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify that the raw data file exists",
    )
    args = parser.parse_args()

    # Resolve the expected location of the Pantheon+ file.
    project_root = Path(__file__).parents[2]
    raw_path = project_root / "data" / "raw" / "Pantheon+_SH0ES.dat"

    if args.verify_only:
        verify_raw_file(raw_path)
        return

    # Placeholder behaviour: create an empty residuals file.
    processed_dir = project_root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    residuals_path = processed_dir / "residuals.csv"
    residuals_path.touch()

    logger = get_logger(__name__)
    logger.info("Created placeholder residuals file at %s", residuals_path)

if __name__ == "__main__":
    main()
