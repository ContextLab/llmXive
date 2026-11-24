"""
generate_calibration_csv.py
---------------------------

This module creates the ``performance_metrics.csv`` file required by the
bootstrap and historical‑window utilities (Task T005).  It reads the raw
JSON calibration snapshots stored in ``data/raw/``, extracts the relevant
performance metrics using the helper functions defined in ``code.fetcher``,
and writes a CSV with the column layout expected by downstream tests and
contracts.

The CSV columns are:
    device_id, timestamp, t1_mean, t2_mean,
    cx_error_mean, readout_error_mean, chip_family

The implementation avoids any synthetic data generation – it only
processes the real JSON snapshots that have been fetched by the
``fetcher`` module.  If no raw snapshots are present, a clear
``RuntimeError`` is raised so that the failure is visible to the
execution harness.
"""

import csv
import logging
from pathlib import Path
from typing import Dict, Any, List

from llmxive_toolkit import paths, get_logger

# Import the performance‑extraction helpers from the fetcher module.
# These functions operate on the raw ``BackendProperties`` dictionary
# format returned by the IBM Quantum API.
from fetcher import (
    extract_performance_metrics,
    extract_chip_family,
)

logger = get_logger(__name__)

def _load_json(file_path: Path) -> Dict[str, Any]:
    """
    Load a JSON file and return its content as a Python ``dict``.

    Parameters
    ----------
    file_path : Path
        Path to the JSON file.

    Returns
    -------
    dict
        Parsed JSON content.

    Raises
    ------
    RuntimeError
        If the file cannot be read or parsed.
    """
    try:
        with file_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load JSON from {file_path}: {e}")
        raise RuntimeError(f"Unable to read JSON file {file_path}") from e

def _mean(values: List[float]) -> float:
    """
    Compute the arithmetic mean of a list of numbers.

    An empty list returns ``float('nan')`` – this mirrors the behaviour
    of the original fetcher implementation and keeps downstream
    handling consistent.

    Parameters
    ----------
    values : List[float]

    Returns
    -------
    float
    """
    if not values:
        return float("nan")
    return sum(values) / len(values)

def _extract_metrics(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Wrapper around ``fetcher.extract_performance_metrics`` that also
    extracts the timestamp and device identifier required for the CSV.

    The raw JSON files written by ``fetcher.fetch_and_save_snapshots``
    contain the keys ``device_id`` and ``timestamp`` in addition to the
    backend properties.  If those keys are missing, a ``RuntimeError`` is
    raised.

    Returns
    -------
    dict
        Mapping of CSV column names to values.
    """
    # Required metadata
    device_id = data.get("device_id")
    timestamp = data.get("timestamp")
    if not device_id or not timestamp:
        raise RuntimeError(
            "Raw JSON snapshot missing required 'device_id' or 'timestamp' fields."
        )

    # Performance metrics (means)
    perf = extract_performance_metrics(data)

    # Chip family (human‑readable)
    chip_family = extract_chip_family(device_id, data)

    # Assemble row dict matching the contract schema
    row = {
        "device_id": device_id,
        "timestamp": timestamp,
        "t1_mean": perf.get("t1_mean"),
        "t2_mean": perf.get("t2_mean"),
        "cx_error_mean": perf.get("cx_error_mean"),
        "readout_error_mean": perf.get("readout_error_mean"),
        "chip_family": chip_family,
    }
    return row

def generate_performance_csv(
    raw_dir: Path = paths.data("raw"),
    output_path: Path = paths.data("processed", "performance_metrics.csv"),
) -> None:
    """
    Generate ``performance_metrics.csv`` from the raw calibration JSON
    snapshots.

    Parameters
    ----------
    raw_dir : Path, optional
        Directory containing raw JSON files.  Defaults to ``data/raw``.
    output_path : Path, optional
        Destination CSV file.  Defaults to
        ``data/processed/performance_metrics.csv``.

    Raises
    ------
    RuntimeError
        If no JSON files are found in ``raw_dir``.
    """
    raw_dir = Path(raw_dir)
    json_files = list(raw_dir.glob("*.json"))
    if not json_files:
        raise RuntimeError(
            f"No raw JSON calibration files found in {raw_dir}. "
            "Ensure that `fetcher.fetch_and_save_snapshots` has been run with a valid IBMQ token."
        )

    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "device_id",
        "timestamp",
        "t1_mean",
        "t2_mean",
        "cx_error_mean",
        "readout_error_mean",
        "chip_family",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for json_path in json_files:
            try:
                data = json.load(json_path.open("r", encoding="utf-8"))
            except Exception as e:
                logger.warning(f"Skipping unreadable file {json_path}: {e}")
                continue

            try:
                row = _extract_metrics(data)
            except RuntimeError as e:
                logger.warning(f"Skipping file {json_path}: {e}")
                continue

            writer.writerow(row)

    logger.info(f"Performance CSV written to {output_path}")

def main() -> None:
    """
    CLI entry point – convenient for manual execution.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate performance_metrics.csv from raw IBM Quantum calibration snapshots."
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=paths.data("raw"),
        help="Directory containing raw JSON snapshots (default: data/raw).",
    )
    parser.add_argument(
        "--out",
        dest="output_path",
        type=Path,
        default=paths.data("processed", "performance_metrics.csv"),
        help="Path to write the generated CSV (default: data/processed/performance_metrics.csv).",
    )
    args = parser.parse_args()
    generate_performance_csv(raw_dir=args.raw_dir, output_path=args.output_path)

if __name__ == "__main__":
    main()