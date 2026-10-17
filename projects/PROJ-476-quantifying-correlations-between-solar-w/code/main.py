"""
Entry point for the solar‑wind composition ↔ geomagnetic indices pipeline.

Provides a minimal CLI that supports the stages required by the
quick‑start documentation:

  python -m code.main --stage all
  python -m code.main --stage fetch --start <YYYY‑MM‑DD> --end <YYYY‑MM‑DD>
  python -m code.main --stage align
  python -m code.main --stage analyze --lags 0,1,2,3,6
  python -m code.main --stage validate
  python -m code.main --help

The implementation deliberately avoids performing any heavy work when
only `--help` is requested, ensuring the verification command exits
cleanly. Full stage implementations delegate to the existing modules
under `code.data`, `code.analysis`, and `code.viz`.
"""
import argparse
import sys
from pathlib import Path

from code import logger

# ----------------------------------------------------------------------
# Helper functions for each pipeline stage
# ----------------------------------------------------------------------


def _run_fetch(start_date: str, end_date: str) -> None:
    """Fetch ACE composition and NOAA geomagnetic data."""
    from code.data.fetch import fetch_ace, fetch_noaa

    logger.info(f"Fetching ACE data for {start_date} → {end_date}")
    ace_path = fetch_ace(start_date, end_date)
    logger.info(f"ACE data written to {ace_path}")

    logger.info(f"Fetching NOAA data for {start_date} → {end_date}")
    noaa_path = fetch_noaa(start_date, end_date)
    logger.info(f"NOAA data written to {noaa_path}")


def _run_align() -> None:
    """Synchronise the raw ACE and NOAA files onto a 1‑hour grid."""
    from code.data.sync import run_sync

    output_path = run_sync()
    logger.info(f"Synchronized dataset written to {output_path}")


def _run_analyze(lags: list[int]) -> None:
    """Perform lagged correlation analysis."""
    from code.analysis.correlation import (
        load_synced_data,
        run_correlation_analysis,
    )

    df = load_synced_data()
    composition_params = ["proton_density", "temperature", "helium_abundance"]
    geomagnetic_indices = ["Kp", "Dst"]
    output_path = Path("results") / "correlations.csv"

    run_correlation_analysis(
        df=df,
        composition_params=composition_params,
        geomagnetic_indices=geomagnetic_indices,
        lags=lags,
        output_path=str(output_path),
    )
    logger.info(f"Correlation results written to {output_path}")


def _run_validate() -> None:
    """Validate correlations on the held‑out period (2018‑2020)."""
    from code.analysis.significance import run_validation_significance
    from code.analysis.correlation import load_synced_data

    df = load_synced_data()
    results = run_validation_significance(df)

    output_path = Path("results") / "validation_correlations.csv"
    results.to_csv(output_path, index=False)
    logger.info(f"Validation results written to {output_path}")


# ----------------------------------------------------------------------
# CLI handling
# ----------------------------------------------------------------------


def _parse_lags(lags_str: str | None) -> list[int]:
    """Convert a comma‑separated lag string into a list of integers."""
    if not lags_str:
        return [0, 1, 2, 3, 6]
    try:
        return [int(item) for item in lags_str.split(",")]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Lags must be integers") from exc


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Solar‑wind composition ↔ geomagnetic indices pipeline. "
            "Use `--stage` to select a processing step."
        )
    )
    parser.add_argument(
        "--stage",
        type=str,
        default="help",
        choices=["all", "fetch", "align", "analyze", "validate", "help"],
        help="Pipeline stage to execute (default: help).",
    )
    parser.add_argument(
        "--start",
        type=str,
        help="Start date (YYYY‑MM‑DD) for the fetch stage.",
    )
    parser.add_argument(
        "--end",
        type=str,
        help="End date (YYYY‑MM‑DD) for the fetch stage.",
    )
    parser.add_argument(
        "--lags",
        type=str,
        help="Comma‑separated list of lag hours for the analysis stage.",
    )

    args = parser.parse_args()

    if args.stage == "help":
        parser.print_help()
        return 0

    if args.stage == "fetch":
        if not args.start or not args.end:
            logger.error("Both --start and --end must be supplied for the fetch stage.")
            return 1
        _run_fetch(args.start, args.end)
        return 0

    if args.stage == "align":
        _run_align()
        return 0

    if args.stage == "analyze":
        lags = _parse_lags(args.lags)
        _run_analyze(lags)
        return 0

    if args.stage == "validate":
        _run_validate()
        return 0

    if args.stage == "all":
        # ``all`` requires explicit date range for the fetch step.
        if not args.start or not args.end:
            logger.error("Both --start and --end are required for the full pipeline.")
            return 1
        _run_fetch(args.start, args.end)
        _run_align()
        _run_analyze(_parse_lags(args.lags))
        _run_validate()
        return 0

    # Should never reach here because argparse restricts choices.
    logger.error(f"Unsupported stage: {args.stage}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
