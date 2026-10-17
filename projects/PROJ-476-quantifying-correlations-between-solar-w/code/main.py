"""
Main entry point for the solar‑wind composition and geomagnetic‑index pipeline.

The script provides a small CLI that can invoke the four major stages
(fetch, align, analyze, validate) individually or run the whole pipeline
with ``--stage all``.  The ``--help`` flag is required by the quick‑start
verification test; it must exit with status 0 and display the usage text.
"""

import argparse
import sys
from pathlib import Path

# Import the package‑level logger; defined in ``code/__init__.py``.
from code import logger

# ----------------------------------------------------------------------
# Helper functions – imported lazily so that ``--help`` does not trigger
# heavy imports or network calls.
# ----------------------------------------------------------------------


def _run_fetch(start_date: str, end_date: str):
    """
    Execute the data‑fetch stage.

    Parameters
    ----------
    start_date, end_date : str
        Date strings in ``YYYY‑MM‑DD`` format.
    """
    if not start_date or not end_date:
        logger.error("Both --start and --end are required for the fetch stage.")
        sys.exit(1)

    # Local imports to avoid pulling heavy modules unless the stage is run.
    from code.data.fetch import fetch_ace, fetch_noaa

    logger.info(f"Fetching ACE data from {start_date} to {end_date}")
    ace_path = fetch_ace(start_date, end_date)

    logger.info(f"Fetching NOAA data from {start_date} to {end_date}")
    noaa_path = fetch_noaa(start_date, end_date)

    return ace_path, noaa_path


def _run_align():
    """
    Execute the alignment (synchronisation) stage.
    """
    from code.data.sync import run_sync

    logger.info("Running data synchronisation (align) stage")
    output_path = run_sync()
    return output_path


def _run_analyze(lags):
    """
    Execute the correlation‑analysis stage.

    Parameters
    ----------
    lags : list[int]
        List of lag hours to test.
    """
    from code.analysis.correlation import (
        load_synced_data,
        run_correlation_analysis,
    )

    logger.info("Running correlation analysis stage")
    df = load_synced_data()
    composition_params = ["proton_density", "temperature", "helium_abundance"]
    geomagnetic_indices = ["Kp", "Dst"]
    output_path = Path("results") / "correlations.csv"
    results_df = run_correlation_analysis(
        df,
        composition_params,
        geomagnetic_indices,
        lags,
        str(output_path),
    )
    return results_df


def _run_validate():
    """
    Execute the validation stage on the held‑out period (2018‑2020).
    """
    from code.analysis.significance import run_validation_significance
    from code.analysis.correlation import load_synced_data

    logger.info("Running validation stage")
    df = load_synced_data()
    validation_df = run_validation_significance(df)
    output_path = Path("results") / "validation_correlations.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    validation_df.to_csv(output_path, index=False)
    logger.info(f"Validation results written to {output_path}")
    return validation_df


# ----------------------------------------------------------------------
# CLI definition
# ----------------------------------------------------------------------


def _build_parser():
    parser = argparse.ArgumentParser(
        prog="python -m code.main",
        description="Solar‑wind composition ↔ geomagnetic‑index pipeline",
    )
    parser.add_argument(
        "--stage",
        choices=["fetch", "align", "analyze", "validate", "all"],
        default="all",
        help="Pipeline stage to execute (default: all)",
    )
    parser.add_argument(
        "--start",
        type=str,
        help="Start date (YYYY‑MM‑DD) for the fetch stage",
    )
    parser.add_argument(
        "--end",
        type=str,
        help="End date (YYYY‑MM‑DD) for the fetch stage",
    )
    parser.add_argument(
        "--lags",
        type=str,
        default="0,1,2,3,6",
        help="Comma‑separated list of lag hours for analysis (default: 0,1,2,3,6)",
    )
    return parser


def main():
    parser = _build_parser()
    args = parser.parse_args()

    # Parse lags into a list of ints for the analysis stage.
    try:
        lags = [int(item) for item in args.lags.split(",") if item.strip() != ""]
    except ValueError:
        logger.error("Invalid value in --lags; must be a comma‑separated list of integers.")
        sys.exit(1)

    # Dispatch based on the selected stage.
    if args.stage == "fetch":
        _run_fetch(args.start, args.end)
    elif args.stage == "align":
        _run_align()
    elif args.stage == "analyze":
        _run_analyze(lags)
    elif args.stage == "validate":
        _run_validate()
    elif args.stage == "all":
        # ``all`` requires a start and end date for the fetch step.
        if not args.start or not args.end:
            logger.error("Both --start and --end are required for the full pipeline.")
            sys.exit(1)

        _run_fetch(args.start, args.end)
        _run_align()
        _run_analyze(lags)
        _run_validate()
    else:
        # This branch should never be hit because argparse restricts choices.
        logger.error(f"Unknown stage: {args.stage}")
        sys.exit(1)

    return 0


if __name__ == "__main__":
    sys.exit(main())