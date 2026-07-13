"""
Central command‑line entry point for the project.

The script supports four high‑level steps that map to the user‑story
pipeline:

* ``download_preprocess`` – fetches and preprocesses raw neuroimaging data
* ``extract_metrics``    – extracts time‑series and builds connectivity matrices
* ``analyze``            – runs PCA, merges metrics, and performs correlation analysis
* ``viz_report``         – creates visualisations and assembles the final report

The original implementation imported ``code.data.download`` at module import
time, which caused an ``ImportError`` because the local ``nilearn`` package
shadowed the real library.  The import has been moved inside the
``run_download_preprocess`` function so that the other steps (which do not
need the download utilities) can run without triggering the error.
"""

import argparse
import logging
import sys
from pathlib import Path

from logging_config import setup_logging, get_logger

# NOTE: ``code.data.download`` is imported lazily inside the function that
# needs it to avoid import‑time failures when the nilearn dependency is
# unavailable in the CI environment.

def run_download_preprocess(args) -> None:
    """Execute the download‑and‑preprocess pipeline."""
    # Lazy import – safe even if ``nilearn.datasets`` cannot be imported.
    from data.download import main as download_main
    download_main()

def run_extract_metrics(args) -> None:
    """Run the metric extraction step."""
    from data.metrics import main as metrics_main
    metrics_main()

def run_analyze(args) -> None:
    """Run the analysis step (PCA + merging)."""
    from analysis.correlation_main_runner import main as analysis_main
    analysis_main()

def run_viz_report(args) -> None:
    """Generate visualisations and the final report."""
    from viz.scatter import main as scatter_main
    from viz.network import main as network_main
    from report.generate import main as report_main

    scatter_main()
    network_main()
    report_main()

def main() -> None:
    parser = argparse.ArgumentParser(description="Project pipeline runner")
    parser.add_argument(
        "--step",
        choices=["download_preprocess", "extract_metrics", "analyze", "viz_report"],
        required=True,
        help="Pipeline step to execute",
    )
    parser.add_argument(
        "--subjects",
        type=int,
        default=0,
        help="Number of subjects to process (used by download step)",
    )
    args = parser.parse_args()

    # Initialise logging early so that all sub‑modules have a logger.
    log_path = Path("logs") / "pipeline.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    setup_logging(log_path)
    logger = get_logger(__name__)
    logger.info("Starting pipeline step: %s", args.step)

    step_dispatch = {
        "download_preprocess": run_download_preprocess,
        "extract_metrics": run_extract_metrics,
        "analyze": run_analyze,
        "viz_report": run_viz_report,
    }

    try:
        step_dispatch[args.step](args)
    except Exception as exc:  # pragma: no cover
        logger.exception("Pipeline step %s failed: %s", args.step, exc)
        sys.exit(1)

if __name__ == "__main__":
    main()