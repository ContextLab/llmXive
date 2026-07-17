import os
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import run_pipeline
from src.results_writer import write_dipole_timeseries
from src.config import DEFAULT_BIN_SIZE_DAYS, get_config_summary

logger = logging.getLogger(__name__)

def load_pipeline_results(
    data_dir: str,
    bin_size_days: int = DEFAULT_BIN_SIZE_DAYS,
    detectors: list = None
) -> list:
    """
    Run the pipeline to generate dipole timeseries results and write to CSV.

    Args:
        data_dir: Base directory for data storage.
        bin_size_days: Bin size in days.
        detectors: List of detectors to process (e.g., ['IceCube', 'Auger']).

    Returns:
        List of result dictionaries.
    """
    if detectors is None:
        detectors = ['IceCube', 'Auger']

    # Ensure output directory exists
    results_dir = Path(data_dir) / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    all_results = []

    for detector in detectors:
        logger.info(f"Processing detector: {detector}")

        # Run pipeline for this detector
        # The pipeline returns a list of results per interval
        try:
            # Note: run_pipeline is expected to return a list of dicts with
            # interval_start, dipole_amp, dipole_phase, quad_amp, partial_interval
            detector_results = run_pipeline(
                detector=detector,
                data_dir=data_dir,
                bin_size_days=bin_size_days
            )

            # Add detector name to each result
            for res in detector_results:
                res['detector'] = detector
                all_results.append(res)

            logger.info(f"Generated {len(detector_results)} intervals for {detector}")

        except Exception as e:
            logger.error(f"Failed to process {detector}: {e}")
            # Continue with other detectors

    # Sort results by interval_start and detector
    all_results.sort(key=lambda x: (x.get('interval_start', ''), x.get('detector', '')))

    return all_results

def main():
    parser = argparse.ArgumentParser(description="Generate dipole timeseries CSV from pipeline results")
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data",
        help="Base directory for data storage (default: data)"
    )
    parser.add_argument(
        "--bin-size",
        type=int,
        default=DEFAULT_BIN_SIZE_DAYS,
        help=f"Bin size in days (default: {DEFAULT_BIN_SIZE_DAYS})"
    )
    parser.add_argument(
        "--detectors",
        type=str,
        nargs="+",
        default=None,
        help="Detectors to process (e.g., IceCube Auger). Default: all"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/results/dipole_timeseries.csv",
        help="Output CSV file path (default: data/results/dipole_timeseries.csv)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info(f"Generating timeseries with bin_size={args.bin_size} days")
    logger.info(f"Data directory: {args.data_dir}")
    logger.info(f"Output file: {args.output}")

    # Run pipeline and collect results
    results = load_pipeline_results(
        data_dir=args.data_dir,
        bin_size_days=args.bin_size,
        detectors=args.detectors
    )

    if not results:
        logger.warning("No results generated. Check pipeline execution.")
        sys.exit(1)

    # Write results to CSV
    write_dipole_timeseries(
        results=results,
        output_path=args.output,
        detectors=args.detectors
    )

    logger.info("Data acquisition completed")
    logger.info(f"Output written to: {args.output}")

if __name__ == "__main__":
    main()