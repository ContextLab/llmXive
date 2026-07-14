"""
Orchestrator script for the llmXive follow‑up project.

This script provides four high‑level phases that can be invoked via
``--phase``:

    * data_prepare      – download the RealEstate10K dataset and stratify it.
    * extract_features  – extract sparse SIFT/ORB features from the stratified data.
    * compute_geometry  – run the sparse epipolar solver and latent warping pipeline.
    * evaluate          – download the dense baseline, run the dense pipeline,
                         compute metrics, statistical analysis, and generate the final
                         verification report.

Each phase simply forwards to the appropriate module ``main`` entry point.
The ``evaluate`` phase also aggregates any memory‑profiler logs produced by
``code/utils/memory_monitor.py`` into ``data/results/metrics.json``.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

# ----------------------------------------------------------------------
# Import configuration utilities (the functions added in ``code/config.py``)
# ----------------------------------------------------------------------
from config import (
    get_results_dir,
    get_raw_dir,
    ensure_directories,
)

# ----------------------------------------------------------------------
# Phase implementations – each calls the corresponding sub‑module ``main``.
# ----------------------------------------------------------------------
def phase_data_prepare() -> None:
    """Download the raw dataset and stratify it into the four strata."""
    from data.download import main as download_main
    from data.stratify import main as stratify_main

    print("[phase_data_prepare] Starting dataset download...")
    download_main()
    print("[phase_data_prepare] Download complete. Starting stratification...")
    stratify_main()
    print("[phase_data_prepare] Stratification complete.")


def phase_extract_features() -> None:
    """Extract sparse SIFT/ORB descriptors for every frame in the stratified set."""
    from data.extract_features import main as extract_main

    print("[phase_extract_features] Extracting sparse features...")
    extract_main()
    print("[phase_extract_features] Feature extraction finished.")


def phase_compute_geometry() -> None:
    """Run the RANSAC fundamental‑matrix solver and the RBF latent‑warping pipeline."""
    from geometry.run_pipeline import main as geometry_main

    print("[phase_compute_geometry] Running geometry pipeline (solver + warp)...")
    geometry_main()
    print("[phase_compute_geometry] Geometry pipeline finished.")


def _aggregate_memory_logs() -> Dict[str, Any]:
    """
    Scan ``data/results`` for any ``*.log`` files written by the memory monitor,
    parse the peak RAM usage (bytes) and wall‑clock time (seconds) and return a
    dictionary suitable for merging into the final ``metrics.json``.
    """
    import re

    results_dir = get_results_dir()
    log_pattern = re.compile(r"Peak RAM:\s*(\d+(?:\.\d+)?)\s*([KMGT]?B)", re.IGNORECASE)
    time_pattern = re.compile(r"Wall‑clock time:\s*([\d\.]+)\s*s", re.IGNORECASE)

    def _parse_size(value: str, unit: str) -> int:
        unit = unit.upper()
        multiplier = {"B": 1, "KB": 1024, "MB": 1024 ** 2, "GB": 1024 ** 3, "TB": 1024 ** 4}
        return int(float(value) * multiplier.get(unit, 1))

    aggregated: Dict[str, Any] = {"memory_logs": []}
    for log_file in results_dir.rglob("*.log"):
        try:
            text = log_file.read_text()
            ram_match = log_pattern.search(text)
            time_match = time_pattern.search(text)
            entry: Dict[str, Any] = {"log_file": str(log_file)}
            if ram_match:
                entry["peak_ram_bytes"] = _parse_size(ram_match.group(1), ram_match.group(2))
            if time_match:
                entry["wall_clock_seconds"] = float(time_match.group(1))
            aggregated["memory_logs"].append(entry)
        except Exception as exc:
            # If a particular log cannot be parsed we still continue.
            print(f"[warning] Could not parse memory log {log_file}: {exc}", file=sys.stderr)

    return aggregated


def phase_evaluate() -> None:
    """
    End‑to‑end evaluation phase:
        1. Download dense baseline frames (if not already present).
        2. Run the dense baseline pipeline.
        3. Compute all metrics (WorldScore, Sparse‑Consistency, FID, etc.).
        4. Run statistical analyses (ANOVA, sensitivity sweep).
        5. Generate the final verification report.
        6. Aggregate memory‑profiler logs into ``metrics.json``.
    """
    from eval.download_dense_baseline import main as download_dense_main
    from eval.run_dense_baseline import main as run_dense_main
    from eval.metrics import main as metrics_main
    from eval.anova import main as anova_main
    from eval.sensitivity import main as sensitivity_main
    from eval.report import main as report_main

    # Ensure output directories exist before any sub‑module runs.
    ensure_directories(get_results_dir(), get_raw_dir())

    print("[phase_evaluate] Downloading dense baseline data...")
    download_dense_main()
    print("[phase_evaluate] Running dense baseline pipeline...")
    run_dense_main()
    print("[phase_evaluate] Computing metrics (WorldScore, Sparse‑Consistency, FID, etc.)...")
    metrics_main()
    print("[phase_evaluate] Performing ANOVA analysis...")
    anova_main()
    print("[phase_evaluate] Running RANSAC sensitivity sweep...")
    sensitivity_main()
    print("[phase_evaluate] Generating final verification report...")
    report_main()

    # ------------------------------------------------------------------
    # Aggregate memory profiling logs into the final metrics JSON.
    # ------------------------------------------------------------------
    metrics_path = get_results_dir() / "metrics.json"
    # Load existing metrics (if any) – the metrics script should have created this.
    if metrics_path.exists():
        try:
            metrics_data = json.loads(metrics_path.read_text())
        except json.JSONDecodeError:
            print("[warning] Existing metrics.json is malformed – starting fresh.", file=sys.stderr)
            metrics_data = {}
    else:
        metrics_data = {}

    memory_info = _aggregate_memory_logs()
    # Merge – later keys overwrite earlier ones if there is a conflict.
    metrics_data.update(memory_info)

    # Write back the enriched JSON.
    metrics_path.write_text(json.dumps(metrics_data, indent=2))
    print(f"[phase_evaluate] Metrics (including memory logs) written to {metrics_path}")


# ----------------------------------------------------------------------
# Argument parsing
# ----------------------------------------------------------------------
def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Project orchestrator – run individual pipeline phases."
    )
    parser.add_argument(
        "--phase",
        type=str,
        required=True,
        choices=["data_prepare", "extract_features", "compute_geometry", "evaluate"],
        help="Which pipeline phase to run.",
    )
    return parser.parse_args(argv)


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv)

    phase_dispatch = {
        "data_prepare": phase_data_prepare,
        "extract_features": phase_extract_features,
        "compute_geometry": phase_compute_geometry,
        "evaluate": phase_evaluate,
    }

    try:
        phase_func = phase_dispatch[args.phase]
    except KeyError:
        print(f"[error] Unknown phase: {args.phase}", file=sys.stderr)
        sys.exit(1)

    phase_func()


if __name__ == "__main__":
    main()
