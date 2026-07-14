"""
Main orchestrator for the llmXive follow‑up project.

This script provides a unified command‑line interface with a ``--phase`` argument
that can be invoked using either the historic aliases (e.g. ``data_prepare``) or
the newer canonical names (e.g. ``prepare``).  Each phase simply forwards the
execution to the appropriate module‑level ``main`` function that already exists
in the code base.

The orchestrator also ensures that all standard project directories exist
before any work is performed.
"""

import argparse
import sys
from pathlib import Path

# Import the public helpers that already exist in the repository.
from config import ensure_directories, get_results_dir, get_config_summary
from data.download import main as download_main
from data.stratify import main as stratify_main
from data.extract_features import main as extract_features_main
from geometry.run_pipeline import main as geometry_pipeline_main
from eval.report import main as report_main

# ----------------------------------------------------------------------
# Helper: map legacy phase names to the current canonical identifiers.
# ----------------------------------------------------------------------
_PHASE_ALIAS_MAP = {
    # canonical : [aliases...]
    "prepare": ["prepare", "data_prepare"],
    "extract": ["extract", "extract_features"],
    "geometry": ["geometry", "compute_geometry"],
    "evaluate": ["evaluate"],
}

def _resolve_phase_name(name: str) -> str:
    """
    Resolve a user‑supplied phase name (which may be a legacy alias) to the
    canonical name used internally.

    Parameters
    ----------
    name: str
        The raw value supplied on the command line.

    Returns
    -------
    str
        One of ``prepare``, ``extract``, ``geometry`` or ``evaluate``.
    """
    name = name.lower()
    for canonical, aliases in _PHASE_ALIAS_MAP.items():
        if name in aliases:
            return canonical
    # If the name is unknown we let the caller decide – raise a clear error.
    raise ValueError(f"Unknown phase '{name}'. Expected one of: "
                     f"{', '.join(sorted({a for al in _PHASE_ALIAS_MAP.values() for a in al}))}")

# ----------------------------------------------------------------------
# Argument parsing
# ----------------------------------------------------------------------
def parse_args(argv: list | None = None):
    """
    Parse command‑line arguments.

    The ``--phase`` argument accepts both the modern identifiers and the
    historic ones; validation is performed after parsing so that argparse does
    not reject the legacy names.
    """
    parser = argparse.ArgumentParser(
        description="Project orchestrator – run a single pipeline phase."
    )
    parser.add_argument(
        "--phase",
        required=True,
        help="Pipeline phase to run (aliases accepted).",
    )
    args = parser.parse_args(argv)

    try:
        args.phase = _resolve_phase_name(args.phase)
    except ValueError as exc:
        parser.error(str(exc))

    return args

# ----------------------------------------------------------------------
# Phase implementations – thin wrappers that delegate to the existing
# module‑level ``main`` functions.
# ----------------------------------------------------------------------
def phase_data_prepare():
    """
    Data preparation phase:
    1. Download the RealEstate10K dataset.
    2. Stratify the dataset into the four required strata.
    """
    ensure_directories()  # create the standard directory tree
    print("[main] Starting data download …")
    download_main()
    print("[main] Stratifying dataset …")
    stratify_main()
    print("[main] Data preparation completed.")

def phase_extract_features():
    """
    Feature‑extraction phase – extracts sparse SIFT/ORB descriptors from the
    stratified keyframes.
    """
    ensure_directories()
    print("[main] Extracting sparse features …")
    extract_features_main()
    print("[main] Feature extraction completed.")

def phase_compute_geometry():
    """
    Geometry computation phase – runs the sparse epipolar solver and the
    latent‑space warping pipeline, then aggregates the warped frames.
    """
    ensure_directories()
    print("[main] Running geometry pipeline (solver + warp) …")
    geometry_pipeline_main()
    print("[main] Geometry computation completed.")

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
