"""
Aggregate raw per‑node run CSV files into a single ``execution_runs.csv``
file and invoke the variable‑fit verification step.

The original implementation already provided helper functions for
loading CSVs, JSON files, and merging dropout events.  This version
retains that API surface while adding a call to ``analysis.validation``.
"""

import csv
import json
from pathlib import Path
from collections import defaultdict
from typing import Iterable, Tuple, List, Dict

import pandas as pd

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions – signatures match the public API described in the
# project documentation.
# ----------------------------------------------------------------------
def _load_csv_files(raw_dir: Path) -> Iterable[Tuple[str, List[Dict[str, str]]]]:
    """
    Yield ``(run_id, rows)`` for each ``run_*.csv`` file in ``raw_dir``.
    """
    for csv_path in raw_dir.glob("run_*.csv"):
        run_id = csv_path.stem.split("_", 1)[1]  # e.g. ``run_001.csv`` → ``001``
        with csv_path.open(newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        yield run_id, rows

def _load_json_file(json_path: Path) -> dict:
    """
    Load a JSON file and return its contents.
    """
    with json_path.open() as f:
        return json.load(f)

def _aggregate_run(run_id: str, rows: List[Dict[str, str]]) -> Dict[str, str]:
    """
    Compute a simple aggregated record for a single run.

    The aggregation mirrors the columns present in the reference
    ``execution_runs.csv`` used throughout the project.
    """
    if not rows:
        raise ValueError(f"No rows to aggregate for run {run_id}")

    # Convert numeric fields to float for aggregation
    ops = [float(r["ops_per_sec"]) for r in rows if r.get("ops_per_sec")]
    wall_times = [float(r["wall_clock_time_sec"]) for r in rows if r.get("wall_clock_time_sec")]

    # Basic aggregation – averages where appropriate
    agg = {
        "run_id": run_id,
        "node_count": str(len(rows)),
        "granularity_setting": rows[0].get("granularity", ""),
        "injected_latency_ms": rows[0].get("injected_latency_ms", ""),
        "throughput_ops": f"{sum(ops) / len(ops):.2f}" if ops else "",
        "mean_wall_clock_time_sec": f"{sum(wall_times) / len(wall_times):.3f}" if wall_times else "",
        "coordination_overhead_ratio": "0.0",  # placeholder – real value computed elsewhere
        "dropout_count": "0",  # placeholder – real value from dropout events
        "packet_to_mbps_factor": "",  # filled later by calibration step
        "percent_to_ops_factor": "",  # filled later by calibration step
    }
    return agg

def _merge_dropout_events(dropout_events: List[dict], run_id: str) -> int:
    """
    Return the number of dropout events for the given ``run_id``.
    """
    return sum(1 for ev in dropout_events if ev.get("run_id") == run_id)

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> int:
    """
    Aggregate all ``run_*.csv`` files under ``data/raw/`` into a single
    ``execution_runs.csv`` file under ``data/processed/`` and then run the
    variable‑fit verification step.
    """
    raw_dir = paths.raw()
    processed_dir = paths.processed()
    processed_dir.mkdir(parents=True, exist_ok=True)

    aggregated: List[Dict[str, str]] = []

    for run_id, rows in _load_csv_files(raw_dir):
        agg = _aggregate_run(run_id, rows)
        aggregated.append(agg)

    # Write the aggregated CSV
    out_csv = processed_dir / "execution_runs.csv"
    if aggregated:
        fieldnames = list(aggregated[0].keys())
        with out_csv.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(aggregated)
        log.info("Wrote aggregated execution runs to %s", out_csv)
    else:
        log.warning("No run CSV files found in %s", raw_dir)

    # ------------------------------------------------------------------
    # Invoke the variable‑fit verification step.
    # ------------------------------------------------------------------
    try:
        from analysis.validation import main as validate
    except Exception as exc:  # pragma: no cover – defensive
        log.error("Failed to import validation module: %s", exc)
        raise

    validate()
    return 0
