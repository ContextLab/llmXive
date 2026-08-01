"""
CI verification script for network connectivity success rate.

This script is intended to be used in the continuous‑integration pipeline.
It reads a JSON metrics file produced by the network generation stage
(typically ``data/analysis/connectivity_metrics.json``) and checks the overall
connectivity success rate.  If the success rate is below the required 95 %,
the script exits with a non‑zero status code, causing the CI job to fail.

Expected JSON format (example):
{
    "total_realizations": 1000,
    "successful_realizations": 960,
    "success_rate": 0.96
}

Only the ``success_rate`` field is required; the other fields are optional
and useful for human‑readable reporting.
"""

import json
import sys
from pathlib import Path

# Path to the connectivity metrics JSON file.
# The network generation code should write this file after processing the
# entire ensemble (including any retry attempts).
METRICS_FILE = Path("data/analysis/connectivity_metrics.json")

# Required minimum success rate (95 %).
MIN_SUCCESS_RATE = 0.95


def load_metrics(path: Path) -> dict:
    """Load the JSON metrics file.

    Parameters
    ----------
    path: Path
        Path to the JSON file.

    Returns
    -------
    dict
        Parsed JSON content.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    json.JSONDecodeError
        If the file contents are not valid JSON.
    """
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_success_rate(metrics: dict) -> float:
    """Extract the success rate from the metrics dict.

    The function prefers an explicit ``success_rate`` key; if it is missing
    it will compute the rate from ``successful_realizations`` and
    ``total_realizations`` when both are present.

    Parameters
    ----------
    metrics: dict
        Dictionary loaded from the JSON file.

    Returns
    -------
    float
        Success rate in the range [0, 1].

    Raises
    ------
    ValueError
        If the required information cannot be determined.
    """
    if "success_rate" in metrics:
        return float(metrics["success_rate"])

    # Fallback computation
    try:
        successful = int(metrics["successful_realizations"])
        total = int(metrics["total_realizations"])
    except KeyError as exc:
        raise ValueError(
            "Metrics JSON must contain either 'success_rate' or both "
            "'successful_realizations' and 'total_realizations'."
        ) from exc

    if total == 0:
        raise ValueError("Total number of realizations cannot be zero.")
    return successful / total


def main() -> None:
    """Entry point for the CI check."""
    if not METRICS_FILE.is_file():
        print(
            f"[CI CONNECTIVITY CHECK] ERROR: Metrics file not found at "
            f"'{METRICS_FILE}'.", file=sys.stderr
        )
        sys.exit(2)  # distinct exit code for missing file

    try:
        metrics = load_metrics(METRICS_FILE)
    except (json.JSONDecodeError, OSError) as exc:
        print(
            f"[CI CONNECTIVITY CHECK] ERROR: Unable to read metrics file: {exc}",
            file=sys.stderr,
        )
        sys.exit(3)

    try:
        success_rate = get_success_rate(metrics)
    except ValueError as exc:
        print(
            f"[CI CONNECTIVITY CHECK] ERROR: Invalid metrics content: {exc}",
            file=sys.stderr,
        )
        sys.exit(4)

    if success_rate < MIN_SUCCESS_RATE:
        print(
            f"[CI CONNECTIVITY CHECK] FAILURE: Connectivity success rate "
            f"{success_rate:.2%} is below the required threshold of "
            f"{MIN_SUCCESS_RATE:.2%}.",
            file=sys.stderr,
        )
        sys.exit(1)
    else:
        print(
            f"[CI CONNECTIVITY CHECK] SUCCESS: Connectivity success rate "
            f"{success_rate:.2%} meets the required threshold of "
            f"{MIN_SUCCESS_RATE:.2%}."
        )
        sys.exit(0)


if __name__ == "__main__":
    main()