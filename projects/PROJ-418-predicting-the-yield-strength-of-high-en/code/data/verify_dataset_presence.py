"""verify_dataset_presence.py

Task T016 – Verify dataset availability before proceeding.

This script checks that the raw HEA dataset file
``data/raw/heas_raw.csv`` exists and contains at least the minimum
number of records required for the downstream power‑analysis step
(FR‑015). If the file is missing or contains too few rows, the script
aborts with a clear, spec‑compliant error message.

The required record count can be supplied explicitly via the
``--min-records`` CLI flag. If omitted, the script attempts to read the
required count from ``data/results/power_analysis.json`` (the artifact
produced by the power‑analysis task). If that file is unavailable, a
conservative default of **50** records is used.

The script exits with status ``0`` when the dataset passes the checks,
otherwise it raises ``SystemExit`` with a non‑zero code, causing the
pipeline to abort.
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

DEFAULT_MIN_RECORDS = 50
POWER_ANALYSIS_JSON = paths.results("power_analysis.json")
RAW_DATA_PATH = paths.data("raw", "heas_raw.csv")


def _load_required_min_records(explicit_min: int | None) -> int:
    """
    Determine the minimum number of records required.

    1. If the caller supplied an explicit ``explicit_min`` value, use it.
    2. Otherwise, try to read ``required_n`` from the power‑analysis JSON
       artifact (if it exists).
    3. Fallback to ``DEFAULT_MIN_RECORDS``.
    """
    if explicit_min is not None:
        return explicit_min

    if POWER_ANALYSIS_JSON.is_file():
        try:
            with POWER_ANALYSIS_JSON.open("r", encoding="utf-8") as f:
                data = json.load(f)
            required_n = data.get("required_n")
            if isinstance(required_n, int) and required_n > 0:
                log.debug(
                    "Using required_n=%d from %s",
                    required_n,
                    POWER_ANALYSIS_JSON,
                )
                return required_n
        except Exception as exc:  # pragma: no cover – defensive
            log.warning(
                "Failed to read required record count from %s: %s",
                POWER_ANALYSIS_JSON,
                exc,
            )

    log.debug(
        "Falling back to default minimum record count of %d", DEFAULT_MIN_RECORDS
    )
    return DEFAULT_MIN_RECORDS


def verify_dataset_presence(min_records: int | None = None) -> None:
    """
    Verify that the raw dataset exists and meets the minimum size.

    Parameters
    ----------
    min_records : int | None
        Minimum number of records required. If ``None`` the function will
        attempt to infer the value from the power‑analysis artifact or
        fall back to ``DEFAULT_MIN_RECORDS``.

    Raises
    ------
    FileNotFoundError
        If ``data/raw/heas_raw.csv`` does not exist.
    ValueError
        If the dataset contains fewer rows than required.
    """
    # Resolve the required threshold
    required = _load_required_min_records(min_records)

    # Check file existence
    if not RAW_DATA_PATH.is_file():
        raise FileNotFoundError(
            f"Required dataset not found at {RAW_DATA_PATH}. "
            "Please ensure the verified Zenodo dataset has been downloaded."
        )

    # Count rows (ignore header only)
    try:
        df = pd.read_csv(RAW_DATA_PATH)
    except Exception as exc:  # pragma: no cover – defensive
        raise RuntimeError(f"Failed to read CSV at {RAW_DATA_PATH}: {exc}") from exc

    record_count = len(df)
    log.info(
        "Dataset %s contains %d records; required minimum is %d.",
        RAW_DATA_PATH,
        record_count,
        required,
    )

    if record_count < required:
        raise ValueError(
            f"Dataset at {RAW_DATA_PATH} contains only {record_count} records, "
            f"which is fewer than the required {required} records for the "
            "statistical power analysis (FR‑015)."
        )

    log.info("Dataset verification passed.")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Verify that the raw HEA dataset exists and meets the minimum "
            "record count required for power analysis (FR‑015)."
        )
    )
    parser.add_argument(
        "--min-records",
        type=int,
        default=None,
        help=(
            "Explicit minimum number of records required. If omitted the "
            "script will try to read the value from "
            f"{POWER_ANALYSIS_JSON} or fall back to a default of {DEFAULT_MIN_RECORDS}."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    args = _parse_args(argv)

    try:
        verify_dataset_presence(min_records=args.min_records)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        log.error(str(exc))
        # Exit with a non‑zero status to abort the pipeline
        sys.exit(1)

    return 0


if __name__ == "__main__":
    sys.exit(main())
