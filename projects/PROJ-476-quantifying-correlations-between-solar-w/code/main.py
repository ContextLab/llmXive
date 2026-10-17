"""
Main entry point for the Solar Wind Geomagnetic Correlation Pipeline.

Quick-start (see specs/001-quantifying-correlations-between-solar-w/quickstart.md):

    python -m code.main --stage all

All heavy/sibling modules are imported lazily inside the stage runners so
that ``--help`` (and argument parsing) never triggers network access or
imports of optional analysis modules.
"""
import os
import sys
import argparse
from datetime import datetime

# Project-relative constants (lightweight, always importable)
RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"
RESULTS_DIR = "results"
FIGURES_DIR = "figures"
ACE_RAW = os.path.join(RAW_DIR, "ace_raw.csv")
NOAA_RAW = os.path.join(RAW_DIR, "noaa_raw.csv")
SYNCED_CSV = os.path.join(PROCESSED_DIR, "synced.csv")
CORRELATIONS_CSV = os.path.join(RESULTS_DIR, "correlations.csv")
VALIDATION_CSV = os.path.join(RESULTS_DIR, "validation_correlations.csv")

COMPOSITION_PARAMS = ["proton_density", "temperature", "helium_abundance"]
GEOMAGNETIC_INDICES = ["Kp", "Dst"]
DEFAULT_LAGS = [0, 1, 2, 3, 6]

STAGES = ["fetch", "align", "analyze", "validate", "all"]


def ensure_layout():
    """Create the project directory hierarchy (idempotent)."""
    for d in (RAW_DIR, PROCESSED_DIR, RESULTS_DIR, FIGURES_DIR):
        os.makedirs(d, exist_ok=True)


def _logger():
    from code import logger
    return logger


def run_fetch(start_date, end_date):
    """Stage: download raw ACE and NOAA data (real sources only)."""
    log = _logger()
    log.info("--- Stage fetch: acquiring real ACE/NOAA data ---")
    from code.data.fetch import fetch_ace, fetch_noaa
    ace_path = fetch_ace(start_date, end_date)
    log.info("ACE data written to %s", ace_path)
    noaa_path = fetch_noaa(start_date, end_date)
    log.info("NOAA data written to %s", noaa_path)


def run_align(ace_path=ACE_RAW, noaa_path=NOAA_RAW, output_path=SYNCED_CSV):
    """Stage: align to 1-hour UTC grid and write data/processed/synced.csv."""
    log = _logger()
    log.info("--- Stage align: synchronising to hourly grid ---")
    from code.data.align import run_alignment, write_synced_csv
    aligned = run_alignment(ace_path, noaa_path)
    write_synced_csv(aligned, output_path)
    log.info("Synced data written to %s", output_path)


def run_analyze(data_path=SYNCED_CSV, lags=None, output_path=CORRELATIONS_CSV):
    """Stage: lagged correlation analysis on the full synced series."""
    log = _logger()
    log.info("--- Stage analyze: lagged correlations ---")
    from code.analysis.correlation import load_synced_data, run_correlation_analysis
    if lags is None:
        lags = DEFAULT_LAGS
    df = load_synced_data(data_path)
    run_correlation_analysis(
        df,
        COMPOSITION_PARAMS,
        GEOMAGNETIC_INDICES,
        lags,
        output_path,
    )
    log.info("Correlation results written to %s", output_path)


def run_validate(data_path=SYNCED_CSV, output_path=VALIDATION_CSV):
    """Stage: held-out 2018-2020 validation correlations."""
    log = _logger()
    log.info("--- Stage validate: held-out period significance ---")
    import pandas as pd
    from code.analysis.significance import run_validation_significance
    df = pd.read_csv(data_path, parse_dates=["timestamp"])
    results = run_validation_significance(df, lags=DEFAULT_LAGS)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    results.to_csv(output_path, index=False)
    log.info("Validation results written to %s", output_path)


def run_all(start_date, end_date, lags):
    log = _logger()
    log.info("Pipeline started at %s", datetime.now().isoformat())
    run_fetch(start_date, end_date)
    run_align()
    run_analyze(lags=lags)
    run_validate()
    log.info("Pipeline completed successfully.")


def build_parser():
    parser = argparse.ArgumentParser(
        prog="python -m code.main",
        description=(
            "Solar wind composition vs. geomagnetic indices correlation "
            "pipeline (ACE + NOAA data)."
        ),
    )
    parser.add_argument(
        "--stage",
        choices=STAGES,
        default="all",
        help="Pipeline stage to run (default: all).",
    )
    parser.add_argument(
        "--start",
        default="1998-01-01",
        help="Start date for data fetch, YYYY-MM-DD (default: 1998-01-01).",
    )
    parser.add_argument(
        "--end",
        default="2020-12-31",
        help="End date for data fetch, YYYY-MM-DD (default: 2020-12-31).",
    )
    parser.add_argument(
        "--lags",
        default="0,1,2,3,6",
        help="Comma-separated lag hours (default: 0,1,2,3,6).",
    )
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    ensure_layout()
    lags = [int(x) for x in args.lags.split(",") if x.strip() != ""]
    if args.stage == "fetch":
        run_fetch(args.start, args.end)
    elif args.stage == "align":
        run_align()
    elif args.stage == "analyze":
        run_analyze(lags=lags)
    elif args.stage == "validate":
        run_validate()
    elif args.stage == "all":
        run_all(args.start, args.end, lags)
    else:  # pragma: no cover
        parser = build_parser()
        parser.error(f"unknown stage: {args.stage}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
