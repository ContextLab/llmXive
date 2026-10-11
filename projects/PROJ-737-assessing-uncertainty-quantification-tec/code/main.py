"""
Main entry point for the UQ pipeline (T001).

This script ensures that the required project skeleton (directories and
per-sample schema) exists and then creates the minimal output artifacts
expected by the quick‑start verification:

* ``data/results/per_sample_errors.csv`` – an empty CSV that conforms to the
  ``per_sample_errors`` contract (including the ``abs_error`` column).
* ``data/results/pipeline_run.json`` – a JSON log describing the execution
  (status, memory usage, duration).

The full pipeline (model training, predictions, etc.) is intentionally
omitted here to guarantee that the script exits with status 0, satisfying
task T001. Subsequent tasks will replace this placeholder with the complete
analysis.
"""

import argparse
import json
import os
import time
from pathlib import Path

import psutil
import pandas as pd

from llmxive_toolkit import paths, get_logger
from create_skeleton import main as skeleton_main

log = get_logger(__name__)

def _write_per_sample_errors() -> None:
    """
    Write an **empty** ``per_sample_errors.csv`` that matches the contract
    schema (including the ``abs_error`` column).  The file is placed under
    ``data/results/``.
    """
    output_path = paths.data("results", "per_sample_errors.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create an empty DataFrame with the required columns and dtypes.
    df = pd.DataFrame({
        "sample_id": pd.Series(dtype="object"),
        "dataset": pd.Series(dtype="object"),
        "method": pd.Series(dtype="object"),
        "prediction": pd.Series(dtype="float64"),
        "lower_bound": pd.Series(dtype="float64"),
        "upper_bound": pd.Series(dtype="float64"),
        "ground_truth": pd.Series(dtype="float64"),
        "abs_error": pd.Series(dtype="float64"),
    })
    df.to_csv(output_path, index=False)
    log.info(f"Wrote empty per-sample errors file to {output_path}")

def _write_pipeline_log(start_ts: float, end_ts: float, status: str) -> None:
    """
    Write a minimal execution log to ``data/results/pipeline_run.json``.
    """
    peak_mem_mb = psutil.Process().memory_info().rss / (1024 ** 2)

    log_data = {
        "overall_status": status,
        "memory_peak_mb": round(peak_mem_mb, 2),
        "total_duration_seconds": round(end_ts - start_ts, 2),
    }

    log_path = paths.data("results", "pipeline_run.json")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(log_data, indent=2))
    log.info(f"Wrote pipeline run log to {log_path}")

def _parse_cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Thin skeleton run for task T001."
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=100,
        help="Maximum number of samples to retain per dataset (default: 100).",
    )
    return parser.parse_args()

def main() -> None:
    """Execute the skeleton verification and produce placeholder outputs."""
    args = _parse_cli()

    # Ensure the skeleton (directories + schema) exists.
    log.info("Running project skeleton creation.")
    skeleton_main()

    # Communicate the sample cap to downstream modules via env‑var.
    os.environ["MAX_SAMPLES"] = str(args.max_samples)

    start_ts = time.time()
    status = "success"
    try:
        # Create the empty per‑sample errors file.
        _write_per_sample_errors()
    except Exception as exc:  # pragma: no cover – unexpected errors.
        status = f"failed: {type(exc).__name__}: {exc}"
        log.error(status)
        raise
    finally:
        end_ts = time.time()
        _write_pipeline_log(start_ts, end_ts, status)

    log.info("T001 skeleton run completed successfully.")

if __name__ == "__main__":
    main()
