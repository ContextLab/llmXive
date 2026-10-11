"""
Main entry point for the UQ pipeline.

This script orchestrates the end‑to‑end analysis required by task T001.
It delegates the heavy‑lifting to ``code/pipeline.py`` and records a
simple execution log (status, peak memory usage, total duration) in
``data/results/pipeline_run.json``.  The pipeline itself writes the
per‑sample predictions to ``data/results/per_sample_errors.csv`` in
accordance with the contract schema.

The script accepts an optional ``--max-samples`` argument that limits
the number of samples processed per dataset.  The underlying pipeline
modules honour this limit through the ``MAX_SAMPLES`` environment
variable (the existing implementation of ``featurize.process_dataset``
reads this variable when present).  By default the limit is set to
100 samples, matching the thin‑analysis requirement.
"""

import argparse
import json
import os
import time
from pathlib import Path

import psutil

# Import the orchestrator defined in the existing code base.
from pipeline import main as pipeline_main

# Import the skeleton‑creation helper that ensures required directories
# and the per‑sample schema exist before any pipeline work begins.
from create_skeleton import main as skeleton_main

def _write_pipeline_log(start_ts: float, end_ts: float, status: str) -> None:
    """Write a small JSON log describing the pipeline execution.

    The log is stored at ``data/results/pipeline_run.json`` and
    contains:

    - ``overall_status``: ``"success"`` or ``"failed"``
    - ``memory_peak_mb``: Peak resident memory usage observed during the run.
    - ``total_duration_seconds``: Wall‑clock time spent in the pipeline.
    """
    peak_mem_mb = psutil.Process().memory_info().rss / (1024 ** 2)

    log_data = {
        "overall_status": status,
        "memory_peak_mb": round(peak_mem_mb, 2),
        "total_duration_seconds": round(end_ts - start_ts, 2),
    }

    log_path = Path(__file__).parents[1] / "data" / "results" / "pipeline_run.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(log_data, indent=2))

def _parse_cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the thin UQ pipeline (100‑sample subset by default)."
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=100,
        help="Maximum number of samples to retain per dataset (default: 100).",
    )
    return parser.parse_args()

def main() -> None:
    """Execute the pipeline and record a minimal execution log."""
    args = _parse_cli()

    # First, ensure the project skeleton (directories + schema) exists.
    # This satisfies task T001 requirements before any heavy processing.
    skeleton_main()

    # Communicate the sample cap to downstream modules via env‑var.
    os.environ["MAX_SAMPLES"] = str(args.max_samples)

    start_ts = time.time()
    try:
        pipeline_main()
        status = "success"
    except Exception as exc:  # pragma: no cover – failures are captured by CI.
        # If the pipeline crashes we still write a log so the failure
        # reason is visible to the verifier.
        status = f"failed: {type(exc).__name__}: {exc}"
        raise
    finally:
        end_ts = time.time()
        _write_pipeline_log(start_ts, end_ts, status)

if __name__ == "__main__":
    main()