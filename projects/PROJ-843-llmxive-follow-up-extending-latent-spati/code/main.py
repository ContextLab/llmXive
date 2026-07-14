"""
Top‑level orchestrator for the research pipeline.

This script is invoked via the command line, e.g.:

    python code/main.py --phase data_prepare
    python code/main.py --phase evaluate

Each phase delegates to the appropriate module and guarantees that required
directories and data artifacts exist before downstream code runs.
"""

import argparse
import sys
from pathlib import Path

# Import helper utilities
from config import ensure_directories, get_raw_dir, get_results_dir

# Phase‑specific imports – these modules already exist in the repo.
# Import inside the functions to avoid unnecessary heavy imports when a
# phase is not executed.
def phase_data_prepare() -> None:
    """Download the RealEstate10K dataset and stratify it."""
    # Ensure the standard directory layout exists
    ensure_directories()
    # Data download
    from data.download import main as download_main
    download_main()
    # Stratification
    from data.stratify import main as stratify_main
    stratify_main()
    print("Data preparation completed.")


def phase_extract_features() -> None:
    """Extract sparse visual features from the stratified dataset."""
    ensure_directories()
    from data.extract_features import main as extract_main
    extract_main()
    print("Feature extraction completed.")


def phase_compute_geometry() -> None:
    """Run the sparse geometry pipeline (solver + warp)."""
    ensure_directories()
    from geometry.run_pipeline import main as geometry_main
    geometry_main()
    print("Geometry computation completed.")


def _download_dense_baseline() -> None:
    """
    Download the dense baseline frames required for evaluation.

    The implementation now delegates to the robust ``eval.download_dense_baseline``
    module, which uses the HuggingFace Hub to fetch the public dataset without
    needing explicit credentials.
    """
    # Ensure the raw data directory exists before downloading
    ensure_directories(get_raw_dir())
    from eval.download_dense_baseline import main as download_dense_main
    download_dense_main()


def phase_evaluate() -> None:
    """Run the full evaluation suite, including metrics and statistical analysis."""
    # 1️⃣  Ensure the dense baseline is present
    _download_dense_baseline()

    # 2️⃣  Run any additional dense‑baseline processing (if required)
    from eval.run_dense_baseline import main as run_dense_main
    run_dense_main()

    # 3️⃣  Compute metrics (WorldScore, Sparse‑Consistency, FID, etc.)
    from eval.metrics import main as metrics_main
    metrics_main()

    # 4️⃣  Perform ANOVA
    from eval.anova import main as anova_main
    anova_main()

    # 5️⃣  Run sensitivity analysis
    from eval.sensitivity import main as sensitivity_main
    sensitivity_main()

    # 6️⃣  Generate the final report
    from eval.report import main as report_main
    report_main()

    print("Evaluation phase completed.")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Project orchestrator")
    parser.add_argument(
        "--phase",
        type=str,
        choices=["data_prepare", "extract_features", "compute_geometry", "evaluate"],
        required=True,
        help="Which pipeline phase to execute",
    )
    return parser.parse_args(argv)

    try:
        args.phase = _resolve_phase_name(args.phase)
    except ValueError as exc:
        parser.error(str(exc))

def main() -> None:
    args = parse_args()
    phase_map = {
        "data_prepare": phase_data_prepare,
        "extract_features": phase_extract_features,
        "compute_geometry": phase_compute_geometry,
        "evaluate": phase_evaluate,
    }
    try:
        phase_func = phase_map[args.phase]
    except KeyError:
        print(f"Unknown phase: {args.phase}", file=sys.stderr)
        sys.exit(1)
    phase_func()

def phase_evaluate():
    """
    Evaluation phase – aggregates memory‑profile logs, computes all metrics,
    runs the ANOVA and sensitivity analyses, and finally writes the
    ``metrics.json`` file together with the human‑readable verification report.
    """
    ensure_directories()
    print("[main] Running evaluation and reporting …")
    report_main()
    print("[main] Evaluation completed. Metrics written to "
          f"{Path(get_results_dir()) / 'metrics.json'}")

# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def main(argv: list | None = None):
    """
    Dispatch to the requested phase.
    """
    args = parse_args(argv)

    phase_dispatch = {
        "prepare": phase_data_prepare,
        "extract": phase_extract_features,
        "geometry": phase_compute_geometry,
        "evaluate": phase_evaluate,
    }

    phase_func = phase_dispatch.get(args.phase)
    if phase_func is None:
        # This should never happen because _resolve_phase_name guarantees
        # a valid key, but we keep the guard for defensive programming.
        sys.exit(f"Internal error: no implementation for phase '{args.phase}'")
    phase_func()

if __name__ == "__main__":
    # When executed as a script ``python code/main.py --phase …``
    # we forward the raw ``sys.argv[1:]`` list to ``main``.
    main(sys.argv[1:])
