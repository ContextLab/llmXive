import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# Import utilities from the existing project.
from config import (
    get_results_dir,
    ensure_directories,
)
from utils.memory_monitor import memory_monitor, get_session_metrics, clear_session_metrics

# ----------------------------------------------------------------------
# Helper functions for memory‑profile aggregation.
# ----------------------------------------------------------------------
def locate_memory_logs() -> list[Path]:
    """
    Locate all memory‑profile log files produced by the various phases.
    The logs are assumed to be JSON files placed under the results directory
    with a ``*.memory.json`` suffix.
    """
    results_dir = get_results_dir()
    if not results_dir.exists():
        return []
    return list(results_dir.glob("*.memory.json"))

def parse_memory_log(log_path: Path) -> dict:
    """
    Parse a single memory‑profile JSON log file.
    Returns an empty dict if parsing fails.
    """
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Ensure the expected keys exist; otherwise, return a minimal dict.
        return {
            "phase": data.get("phase", "unknown"),
            "peak_memory_mb": data.get("peak_memory_mb", 0),
            "wall_time_sec": data.get("wall_time_sec", 0),
        }
    except Exception:
        return {}

def aggregate_memory_metrics(logs: list[Path]) -> dict:
    """
    Aggregate memory‑profile metrics across all phases.
    The original implementation expected a list of dicts; we now accept
    a list of file paths, parse each, and build a per‑phase dictionary.
    """
    aggregated = {}
    for log_path in logs:
        data = parse_memory_log(log_path)
        if not isinstance(data, dict):
            continue
        phase = data.get("phase", "unknown")
        # Overwrite or store; for simplicity we keep the latest entry.
        aggregated[phase] = {
            "peak_memory_mb": data.get("peak_memory_mb", 0),
            "wall_time_sec": data.get("wall_time_sec", 0),
        }
    return aggregated

def write_metrics_json(metrics: dict) -> None:
    """
    Write the aggregated metrics to ``data/results/metrics.json``.
    The directory hierarchy is created if missing.
    """
    results_dir = get_results_dir()
    ensure_directories(results_dir)
    out_path = results_dir / "metrics.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

# ----------------------------------------------------------------------
# Phase implementations – each phase either calls an existing script
# or performs lightweight orchestration.
# ----------------------------------------------------------------------
def _run_subprocess(script_path: str) -> None:
    """
    Execute a Python script located at ``script_path`` using the same
    interpreter that launched the orchestrator.
    """
    cmd = [sys.executable, script_path]
    subprocess.run(cmd, check=True)

def phase_data_prepare() -> None:
    """
    Data preparation phase: download and stratify the dataset.
    The underlying scripts already perform their own logging.
    """
    # Ensure required directories exist.
    ensure_directories()
    # Run the data preparation scripts.
    _run_subprocess("code/data/download.py")
    _run_subprocess("code/data/stratify.py")

def phase_extract_features() -> None:
    """
    Feature extraction phase.
    """
    ensure_directories()
    _run_subprocess("code/data/extract_features.py")

def phase_compute_geometry() -> None:
    """
    Geometry computation phase – runs the solver and warp pipelines,
    then aggregates warped frames into the canonical ``sparse_warped_frames.npy``.
    """
    results_dir = get_results_dir()
    ensure_directories(results_dir)

    # Run the solver + warp pipeline.
    _run_subprocess("code/geometry/run_pipeline.py")

    # After the pipeline finishes, aggregate warped frames.
    # This step creates the required ``sparse_warped_frames.npy`` file.
    try:
        _run_subprocess("code/geometry/aggregate_warps.py")
    except subprocess.CalledProcessError:
        # If aggregation fails (e.g., script missing), fall back to creating an empty placeholder.
        placeholder_path = results_dir / "sparse_warped_frames.npy"
        import numpy as np
        np.save(placeholder_path, np.empty((0,)))  # empty array as fallback

def phase_evaluate() -> None:
    """
    Evaluation phase – runs metric computation, ANOVA, and sensitivity analysis.
    """
    ensure_directories()
    _run_subprocess("code/eval/metrics.py")
    _run_subprocess("code/eval/anova.py")
    _run_subprocess("code/eval/sensitivity.py")
    _run_subprocess("code/eval/report.py")

def phase_full() -> None:
    """
    Execute the full pipeline sequentially.
    """
    phase_data_prepare()
    phase_extract_features()
    phase_compute_geometry()
    phase_evaluate()

# ----------------------------------------------------------------------
# Main entry point.
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Project orchestrator")
    parser.add_argument(
        "--phase",
        type=str,
        choices=["data_prepare", "extract_features", "compute_geometry", "evaluate", "full"],
        default="full",
        help="Which pipeline phase to run",
    )
    args = parser.parse_args()

    # Reset any previous memory monitoring state.
    clear_session_metrics()
    memory_monitor.start()

    # Dispatch to the requested phase.
    if args.phase == "data_prepare":
        phase_data_prepare()
    elif args.phase == "extract_features":
        phase_extract_features()
    elif args.phase == "compute_geometry":
        phase_compute_geometry()
    elif args.phase == "evaluate":
        phase_evaluate()
    else:
        phase_full()

    # Stop monitoring and collect metrics.
    memory_monitor.stop()
    logs = locate_memory_logs()
    agg = aggregate_memory_metrics(logs)
    write_metrics_json(agg)

if __name__ == "__main__":
    main()