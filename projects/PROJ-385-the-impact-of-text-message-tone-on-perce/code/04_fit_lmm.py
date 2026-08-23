"""
Minimal Linear Mixed Model (LMM) fitting script.

This script is intentionally lightweight for the purpose of the guard task.
It reads the anonymised ratings dataset from the processed data directory,
performs a very simple sanity‑check (counts rows), and exits. In a full
implementation the data would be fed to ``statsmodels.MixedLM``.
"""

import csv
import sys
from pathlib import Path

# Import helper to locate the processed data directory
from config import get_processed_data_dir

# Expected path to the anonymised ratings file
ANON_RATINGS_FILENAME = "anonymised_ratings.csv"


def get_anonymised_ratings_path() -> Path:
    """Return the absolute path to the processed anonymised ratings CSV."""
    processed_dir = get_processed_data_dir()
    return processed_dir / ANON_RATINGS_FILENAME


def load_anonymised_ratings(path: Path):
    """Load the CSV file and return a list of rows (as dictionaries)."""
    if not path.is_file():
        sys.stderr.write(f"Error: Expected processed data file not found: {path}\\n")
        sys.exit(1)

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return rows


def main():
    """Entry point for the LMM script."""
    ratings_path = get_anonymised_ratings_path()
    rows = load_anonymised_ratings(ratings_path)

    # Simple sanity check – report number of rows read
    print(f"Loaded {len(rows)} rows from {ratings_path}")

    # Placeholder for actual LMM fitting logic.
    # In the full pipeline this would invoke statsmodels.MixedLM, etc.
    # For now we just exit successfully.
    sys.exit(0)


if __name__ == "__main__":
    main()
