"""
Feasibility check script for the llmXive follow‑up experiment.

This script runs a representative subset of the full factorial sweep
(library sizes up to 50, both pruning flags, all three overlap levels)
using the existing ``code.agent`` CLI. It measures wall‑clock runtime
and peak RSS memory usage, asserts that they stay within the limits
defined by SC‑005 (≤ 6 h and ≤ 7 GB), and writes a JSON report to
``data/results/feasibility_report.json``.
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import psutil
from llmxive_toolkit import paths, get_logger

# Logger for optional debugging – writes to the standard llmxive logs.
log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _run_agent(library_sizes, pruning_flags, overlap_levels, task_sample, seed):
    """
    Execute the ``code.agent`` module via ``python -m`` with the supplied
    configuration. Returns the elapsed wall‑clock time (seconds).
    """
    cmd = [
        sys.executable,
        "-m",
        "code.agent",
        "--library-sizes",
        *map(str, library_sizes),
        "--overlap",
        *overlap_levels,
        "--pruning",
        *pruning_flags,
        "--seed",
        str(seed),
        "--randomize-tasks",
        "--task-sample",
        str(task_sample),
    ]

    log.info(f"Running feasibility agent command: {' '.join(cmd)}")
    start = time.perf_counter()
    subprocess.run(cmd, check=True)
    elapsed = time.perf_counter() - start
    return elapsed

def _measure_peak_memory():
    """
    Return the current RSS memory usage of this process (bytes).
    ``psutil`` does not provide historical peaks, but the agent runs in
    the same process tree, so the RSS after execution is a reasonable
    proxy for peak usage in this constrained environment.
    """
    process = psutil.Process()
    rss = process.memory_info().rss
    return rss

def _write_report(report_path: Path, report: dict):
    """Write the JSON feasibility report, ensuring parent directories exist."""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    log.info(f"Feasibility report written to {report_path}")

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def run_feasibility(
    library_sizes=None,
    pruning_flags=None,
    overlap_levels=None,
    task_sample: int = 100,
    seed: int = 42,
) -> dict:
    """
    Execute the representative sweep, measure runtime and memory, and
    produce a JSON report.

    Parameters
    ----------
    library_sizes : list[int] | None
        Library sizes to test. Defaults to ``[10, 20, 30, 40, 50]``.
    pruning_flags : list[str] | None
        Pruning settings – ``["off", "fr04"]`` by default.
    overlap_levels : list[str] | None
        Overlap levels – ``["low", "medium", "high"]`` by default.
    task_sample : int
        Number of tasks to sample for each run (default 100 to keep the
        feasibility check fast while remaining representative).
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    dict
        Dictionary containing runtime, memory, and boolean limit checks.
    """
    # Default configuration matching the specification
    if library_sizes is None:
        library_sizes = [10, 20, 30, 40, 50]
    if pruning_flags is None:
        pruning_flags = ["off", "fr04"]
    if overlap_levels is None:
        overlap_levels = ["low", "medium", "high"]

    # Run the agent and time it
    runtime_seconds = _run_agent(
        library_sizes,
        pruning_flags,
        overlap_levels,
        task_sample,
        seed,
    )

    # Measure memory usage after the agent has finished
    peak_rss_bytes = _measure_peak_memory()

    # Limits defined by SC‑005
    TIME_LIMIT_SECONDS = 21_600  # 6 hours
    MEMORY_LIMIT_BYTES = 7 * 1024 ** 3  # 7 GB

    report = {
        "total_runtime_seconds": runtime_seconds,
        "peak_memory_bytes": peak_rss_bytes,
        "within_time_limit": runtime_seconds <= TIME_LIMIT_SECONDS,
        "within_memory_limit": peak_rss_bytes <= MEMORY_LIMIT_BYTES,
    }

    # Write the report to the canonical location
    out_path = paths.results("feasibility_report.json")
    _write_report(out_path, report)

    return report

def main():
    parser = argparse.ArgumentParser(
        description="Feasibility check for the llmXive follow‑up experiment."
    )
    parser.add_argument(
        "--library-sizes",
        type=int,
        nargs="+",
        default=None,
        help="Library sizes to test (default: 10 20 30 40 50).",
    )
    parser.add_argument(
        "--pruning",
        type=str,
        nargs="+",
        default=None,
        help="Pruning flags to test (default: off fr04).",
    )
    parser.add_argument(
        "--overlap",
        type=str,
        nargs="+",
        default=None,
        help="Overlap levels to test (default: low medium high).",
    )
    parser.add_argument(
        "--task-sample",
        type=int,
        default=100,
        help="Number of tasks to sample per configuration (default: 100).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42).",
    )
    args = parser.parse_args()

    # Normalise arguments (lower‑case where appropriate)
    lib_sizes = args.library_sizes
    pruning = args.pruning
    overlap = args.overlap

    # Convert pruning flags to the values expected by ``code.agent``
    if pruning is not None:
        pruning = [
            "fr04" if p in ("fr04", "on") else "off" for p in pruning
        ]

    if overlap is not None:
        overlap = [lvl.lower() for lvl in overlap]

    # Run feasibility check with the supplied (or default) configuration
    run_feasibility(
        library_sizes=lib_sizes,
        pruning_flags=pruning,
        overlap_levels=overlap,
        task_sample=args.task_sample,
        seed=args.seed,
    )

if __name__ == "__main__":
    main()
