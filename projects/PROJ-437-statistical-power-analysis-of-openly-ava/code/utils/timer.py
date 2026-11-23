"""
Simple timing utilities used throughout the pipeline.

The functions are deliberately lightweight and write human‑readable CSV/JSON
files into the ``results/paper`` directory. They are imported by
``code/main.py`` and therefore must exist with the exact signatures used
there.
"""

import csv
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

# Global state – not thread‑safe but sufficient for the single‑process pipeline
_run_start: float | None = None
_splits: List[Tuple[str, float, float, Dict]] = []  # (name, timestamp, elapsed, metadata)

def start_run() -> None:
    """
    Record the start time of the whole pipeline run.
    """
    global _run_start, _splits
    _run_start = time.time()
    _splits = []
    logger.info("Run timer started.")

def end_run() -> None:
    """
    Record the end of the pipeline run. This simply logs the total elapsed
    time; the detailed breakdown is written later via ``save_timing_report``.
    """
    if _run_start is None:
        raise RuntimeError("start_run() must be called before end_run()")
    total_elapsed = time.time() - _run_start
    logger.info(f"Run timer stopped – total elapsed: {total_elapsed:.2f}s")

def log_split(split_name: str, metadata: Dict | None = None) -> None:
    """
    Record a named split (stage) of the pipeline.

    Args:
        split_name: Human‑readable name for the stage.
        metadata: Optional dictionary of free‑form metadata that will be
                  stored alongside the split record.
    """
    if _run_start is None:
        raise RuntimeError("start_run() must be called before log_split()")
    now = time.time()
    elapsed = now - (_splits[-1][1] if _splits else _run_start)
    _splits.append((split_name, now, elapsed, metadata or {}))
    logger.debug(f"Logged split '{split_name}' – elapsed: {elapsed:.2f}s")

def save_timing_report(report_path: Path | str = "results/paper/timing_report.json") -> None:
    """
    Write a JSON summary of the timing information.

    The JSON contains the total runtime and a list of per‑split records.
    """
    if _run_start is None:
        raise RuntimeError("No timing information to save – start_run() not called")
    total_elapsed = time.time() - _run_start
    report = {
        "run_started": datetime.utcfromtimestamp(_run_start).isoformat() + "Z",
        "run_ended": datetime.utcnow().isoformat() + "Z",
        "total_elapsed_seconds": total_elapsed,
        "splits": [
            {
                "name": name,
                "timestamp": datetime.utcfromtimestamp(ts).isoformat() + "Z",
                "elapsed_seconds": elapsed,
                "metadata": meta,
            }
            for name, ts, elapsed, meta in _splits
        ],
    }
    out_path = Path(report_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Timing report written to {out_path}")

def save_timing_breakdown(csv_path: Path | str = "results/paper/timing_breakdown.csv") -> None:
    """
    Write a CSV file that mirrors the format used in the existing test fixture
    ``results/paper/timing_breakdown.csv``.
    """
    if not _splits:
        raise RuntimeError("No split information recorded – cannot write breakdown")
    out_path = Path(csv_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["split_name", "timestamp", "elapsed_seconds", "metadata_json"])
        for name, ts, elapsed, meta in _splits:
            metadata_json = json.dumps(meta, ensure_ascii=False)
            iso_ts = datetime.utcfromtimestamp(ts).isoformat() + "Z"
            writer.writerow([name, iso_ts, f"{elapsed:.2f}", metadata_json])
    logger.info(f"Timing breakdown CSV written to {out_path}")
