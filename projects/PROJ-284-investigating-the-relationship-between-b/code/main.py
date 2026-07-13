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

# NOTE: Importing the heavy `data.metrics` module caused a crash when the
# optional `nilearn` dependency was missing.  The import is now moved inside
# the command handlers so that the rest of the pipeline (e.g. the analysis
# step that merges metrics) can run even if `nilearn` is unavailable.

def run_download_preprocess(args):
    """
    Placeholder for the download‑and‑preprocess step.
    The real implementation lives in `code/data/download.py` and
    `code/data/preprocess.py`.  Here we simply invoke the existing entry
    points, catching import errors so the pipeline can continue to later
    steps when the heavy neuroimaging tools are not installed in CI.
    """
    logger = get_logger()
    try:
        from data.download import main as download_main
        download_main(args.subjects)
    except Exception as exc:  # pragma: no cover
        logger.error("Download/preprocess step failed: %s", exc)
        sys.exit(1)

def run_extract_metrics(args):
    """
    Run the metric extraction pipeline.  The heavy neuroimaging imports are
    performed lazily inside `data.metrics`.
    """
    logger = get_logger()
    try:
        from data.metrics import main as metrics_main
        # The metrics module expects a DataFrame describing subjects.
        # For the purposes of the CI run we construct a minimal stub.
        import pandas as pd

        # Load the phenotypic table that was fetched by the download step.
        phenotypic_path = Path("data/processed/phenotypic.csv")
        if not phenotypic_path.is_file():
            logger.error("Phenotypic file not found at %s", phenotypic_path)
            sys.exit(1)
        subjects_df = pd.read_csv(phenotypic_path)
        metrics_main(subjects_df, atlas_url="https://example.com/schaefer_atlas.zip")
    except Exception as exc:  # pragma: no cover
        logger.error("Metric extraction failed: %s", exc)
        sys.exit(1)

def run_analyze(args):
    """
    Run the correlation/PCA analysis.
    """
    logger = get_logger()
    try:
        from analysis.correlations import main as analysis_main
        analysis_main()
    except Exception as exc:  # pragma: no cover
        logger.error("Analysis step failed: %s", exc)
        sys.exit(1)

def run_viz_report(args):
    """
    Generate visualisations and the final report.
    """
    logger = get_logger()
    try:
        from viz.scatter import main as scatter_main
        from viz.network import main as network_main
        from report.generate import main as report_main

        scatter_main()
        network_main()
        report_main()
    except Exception as exc:  # pragma: no cover
        logger.error("Visualization/report step failed: %s", exc)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Run the full HCP analysis pipeline")
    subparsers = parser.add_subparsers(dest="step")

    # download_preprocess
    dp_parser = subparsers.add_parser("download_preprocess", help="Download and preprocess data")
    dp_parser.add_argument("--subjects", type=int, default=10, help="Number of subjects to process")

    # extract_metrics
    em_parser = subparsers.add_parser("extract_metrics", help="Extract network metrics")

    # analyze
    subparsers.add_parser("analyze", help="Run PCA and correlation analysis")

    # viz_report
    subparsers.add_parser("viz_report", help="Generate plots and final report")

    args = parser.parse_args()

    # Initialise logging as early as possible
    setup_logging()
    logger = get_logger()
    logger.info("Starting pipeline step: %s", args.step)

    if args.step == "download_preprocess":
        run_download_preprocess(args)
    elif args.step == "extract_metrics":
        run_extract_metrics(args)
    elif args.step == "analyze":
        run_analyze(args)
    elif args.step == "viz_report":
        run_viz_report(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()