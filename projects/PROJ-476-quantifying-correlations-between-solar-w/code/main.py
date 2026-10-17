import argparse
import sys
from pathlib import Path
from llmxive_toolkit import get_logger

# Import from the API surface defined in the project
try:
    from code.data.fetch_ace import fetch_ace
    from code.data.fetch_noaa import fetch_noaa
    from code.data.sync import run_sync
    from code.analysis.correlation import run_correlation_analysis
    from code.analysis.significance import run_validation_significance
except ImportError as e:
    # We handle imports inside the stage functions to avoid 
    # crashing --help if some modules aren't fully implemented yet
    pass

log = get_logger(__name__)

def _run_fetch(start, end):
    log.info(f"Fetching data from {start} to {end}...")
    fetch_ace(start, end)
    fetch_noaa(start, end)

def _run_align():
    log.info("Aligning and synchronizing data...")
    run_sync()

def _run_analyze(lags):
    log.info(f"Running correlation analysis with lags {lags}...")
    # This typically uses the synced.csv and writes to results/correlations.csv
    # The actual logic is inside run_correlation_analysis
    run_correlation_analysis()

def _run_validate():
    log.info("Running validation on held-out period...")
    run_validation_significance()

def main():
    parser = argparse.ArgumentParser(
        description="Quantifying Correlations Between Solar Wind Composition and Geomagnetic Indices"
    )
    parser.add_argument(
        "--stage", 
        choices=["fetch", "align", "analyze", "validate", "all"], 
        required=False,
        help="Pipeline stage to execute"
    )
    parser.add_argument("--start", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", help="End date (YYYY-MM-DD)")
    parser.add_argument("--lags", default="0,1,2,3,6", help="Comma-separated list of lags in hours")

    args = parser.parse_args()

    if args.stage is None:
        parser.print_help()
        return 0

    # Defaults for the full pipeline if not provided
    start = args.start or "1998-01-01"
    end = args.end or "2020-12-31"
    lags_list = [int(x) for x in args.lags.split(",")]

    try:
        if args.stage == "fetch":
            if not args.start or not args.end:
                log.error("Both --start and --end are required for the fetch stage.")
                sys.exit(1)
            _run_fetch(args.start, args.end)
        elif args.stage == "align":
            _run_align()
        elif args.stage == "analyze":
            _run_analyze(lags_list)
        elif args.stage == "validate":
            _run_validate()
        elif args.stage == "all":
            _run_fetch(start, end)
            _run_align()
            _run_analyze(lags_list)
            _run_validate()
        
        log.info(f"Stage {args.stage} completed successfully.")
    except Exception as e:
        log.exception(f"Pipeline failed during stage {args.stage}: {e}")
        sys.exit(1)

    return 0

if __name__ == "__main__":
    sys.exit(main())
