"""
Main entry point for the Solar Wind Composition and Geomagnetic Indices pipeline.
Provides a CLI to run specific stages or the entire pipeline.
"""
import argparse
import sys
from code import logger

def run_fetch(args):
    from code.data.fetch_ace import fetch_ace
    from code.data.fetch_noaa import fetch_noaa
    start = args.start or "1998-01-01"
    end = args.end or "2020-12-31"
    logger.info(f"Stage: Fetching data from {start} to {end}")
    fetch_ace(start, end)
    fetch_noaa(start, end)

def run_align():
    from code.data.sync import run_sync
    logger.info("Stage: Aligning and synchronizing datasets")
    run_sync()

def run_analyze(args):
    from code.analysis.run_correlation import main as run_corr
    logger.info("Stage: Computing lagged correlations")
    run_corr()

def run_validate():
    from code.analysis.significance import run_validation_significance
    from code.config import SYNCED_CSV
    import pandas as pd
    logger.info("Stage: Validating on held-out period")
    try:
        df = pd.read_csv(SYNCED_CSV, parse_dates=["timestamp"])
        run_validation_significance(df)
    except FileNotFoundError:
        logger.error(f"Cannot validate: {SYNCED_CSV} not found. Run 'align' first.")

def main():
    parser = argparse.ArgumentParser(
        description="Quantifying Correlations Between Solar Wind Composition and Geomagnetic Indices"
    )
    parser.add_argument(
        "--stage", 
        choices=["fetch", "align", "analyze", "validate", "all"], 
        help="Pipeline stage to execute"
    )
    parser.add_argument("--start", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--lags", type=str, help="Comma-separated lags (e.g., 0,1,2,3,6)")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    if args.stage == "all":
        run_fetch(args)
        run_align()
        run_analyze(args)
        run_validate()
    elif args.stage == "fetch":
        run_fetch(args)
    elif args.stage == "align":
        run_align()
    elif args.stage == "analyze":
        run_analyze(args)
    elif args.stage == "validate":
        run_validate()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
