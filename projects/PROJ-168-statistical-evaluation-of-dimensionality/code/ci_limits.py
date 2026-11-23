"""ci_limits.py
Lightweight CI script to enforce resource limits.

Reads `results/monitoring.csv` (or a user‑provided CSV file), checks the two SC limits:
  * SC-003: peak RAM usage must not exceed 7 GB (7_000_000_000 bytes)
  * SC-004: total wall‑clock time must not exceed 6 h (21 600 seconds)

If any limit is violated the script prints a clear message to stderr and exits
with status code 1; otherwise it prints a success message and exits with status 0.

The script can be invoked in two ways:

1. Default usage (no arguments):
   ```bash
   python -m ci_limits
   ```
   This reads the canonical monitoring file at `results/monitoring.csv`.

2. Custom CSV for testing:
   ```bash
   python -m ci_limits path/to/custom_monitoring.csv
   ```
   This is useful for unit tests that deliberately supply violating data.
"""
import sys
from pathlib import Path

import pandas as pd
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Thresholds (bytes and seconds)
RAM_LIMIT_BYTES = 7_000_000_000
TIME_LIMIT_SECONDS = 21_600

def _load_monitoring_csv(csv_path: Path) -> pd.DataFrame:
    """Load the monitoring CSV and perform basic validation.

    Parameters
    ----------
    csv_path : Path
        Path to the CSV file to read.

    Returns
    -------
    pd.DataFrame
        DataFrame with at least ``wall_time_s`` and ``peak_ram_bytes`` columns.

    Exits
    -----
    The function calls ``sys.exit`` with code 1 on any error to keep the
    script behaviour simple and consistent with the original implementation.
    """
    if not csv_path.exists():
        log.error(f"Monitoring file not found: {csv_path}")
        sys.exit(1)
    try:
        df = pd.read_csv(csv_path)
    except Exception as exc:  # pragma: no cover
        log.error(f"Failed to read '{csv_path}': {exc}")
        sys.exit(1)

    required_cols = {"wall_time_s", "peak_ram_bytes"}
    missing = required_cols.difference(df.columns)
    if missing:
        log.error(f"Monitoring CSV missing required columns: {missing}")
        sys.exit(1)
    return df

def _determine_csv_path() -> Path:
    """Determine which CSV file to read.

    If a command‑line argument is supplied, it is interpreted as a path to a
    CSV file. Otherwise the default ``results/monitoring.csv`` is used.
    """
    if len(sys.argv) > 1:
        # The first argument after the script name is taken as the CSV path.
        candidate = Path(sys.argv[1])
        if candidate.is_dir():
            log.error(f"Provided path is a directory, not a CSV file: {candidate}")
            sys.exit(1)
        return candidate
    # Default location using llmxive_toolkit helper (creates parent dirs if needed)
    return paths.results("monitoring.csv")

def main() -> None:
    """Entry point for the CI limits checker."""
    monitoring_path = _determine_csv_path()
    df = _load_monitoring_csv(monitoring_path)

    total_wall_time = df["wall_time_s"].sum()
    max_peak_ram = df["peak_ram_bytes"].max()

    violations = []

    if max_peak_ram > RAM_LIMIT_BYTES:
        violations.append(
            f"SC-003 violation: peak RAM usage {max_peak_ram:,} bytes "
            f"> limit {RAM_LIMIT_BYTES:,} bytes"
        )
    if total_wall_time > TIME_LIMIT_SECONDS:
        violations.append(
            f"SC-004 violation: total wall‑time {total_wall_time:,} seconds "
            f"> limit {TIME_LIMIT_SECONDS:,} seconds"
        )

    if violations:
        for msg in violations:
            print(msg, file=sys.stderr)
        sys.exit(1)

    # All good – print a success message
    print("CI limits check passed: peak RAM and total wall‑time within limits.")
    sys.exit(0)

if __name__ == "__main__":
    main()