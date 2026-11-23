"""
src/cli/validate_data.py
-------------------------

Simple validation utility used by the Quick‑Start guide.  It walks the supplied
directory, looks for Parquet files, and checks that each contains the required
columns:

    step_index, coherence_score, diversity_score, latency_ms, engine_type

If any file is missing a column or cannot be read, the script exits with a
non‑zero status code, causing the CI run to fail – this mirrors the behaviour
expected by the original quick‑start documentation.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd
from llmxive_toolkit import get_logger

log = get_logger(__name__)

REQUIRED_COLUMNS = {
    "step_index",
    "coherence_score",
    "diversity_score",
    "latency_ms",
    "engine_type",
}


def validate_parquet_file(parquet_path: Path) -> bool:
    """Return ``True`` if the parquet file contains all required columns."""
    try:
        df = pd.read_parquet(parquet_path, engine="pyarrow")
    except Exception as exc:
        log.error("Failed to read %s: %s", parquet_path, exc)
        return False

    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        log.error("File %s is missing columns: %s", parquet_path, ", ".join(sorted(missing)))
        return False

    log.info("Validated %s (%d rows).", parquet_path, len(df))
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate Parquet metric files produced by the simulation."
    )
    parser.add_argument(
        "--path",
        type=str,
        required=True,
        help="Directory containing Parquet files to validate.",
    )
    args = parser.parse_args()

    base_dir = Path(args.path)
    if not base_dir.is_dir():
        log.error("Provided path %s is not a directory.", base_dir)
        sys.exit(1)

    parquet_files = list(base_dir.rglob("*.parquet"))
    if not parquet_files:
        log.error("No Parquet files found under %s.", base_dir)
        sys.exit(1)

    all_ok = True
    for p in parquet_files:
        if not validate_parquet_file(p):
            all_ok = False

    if not all_ok:
        log.error("One or more validation checks failed.")
        sys.exit(1)

    log.info("All Parquet files passed validation.")
    sys.exit(0)


if __name__ == "__main__":
    main()
