"""
code/profile_smoothness.py: Performance profiling for smoothness analysis.

This module profiles the `code/smoothness.py` loop using cProfile to identify
performance bottlenecks in the factorization and counting logic.
"""
import cProfile
import pstats
import io
import os
import sys
import argparse
import logging
from typing import Optional

# Add project root to path to import sibling modules
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from smoothness import load_primes_from_csv, count_smooth_in_interval, setup_logging

def profile_smoothness_analysis(
    x: int,
    h: int,
    y: int,
    primes_path: str,
    output_path: str
) -> None:
    """
    Profile the smoothness analysis loop and save results to a text file.

    Args:
        x: Start of the interval.
        h: Length of the interval.
        y: Smoothness bound.
        primes_path: Path to the CSV file containing primes.
        output_path: Path where the profiling report will be saved.
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Load primes once before profiling to isolate the loop cost
    # We assume the prime list is already in memory or loaded quickly enough
    # that the profiling focuses on the interval loop.
    primes = load_primes_from_csv(primes_path)

    # Create a cProfile instance
    profiler = cProfile.Profile()

    # Define the function to profile
    def run_target():
        count_smooth_in_interval(x, h, y, primes)

    # Run the profiler
    profiler.enable()
    try:
        run_target()
    finally:
        profiler.disable()

    # Sort stats by cumulative time
    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats('cumulative')

    # Print top 50 functions to the stream
    stats.print_stats(50)

    # Write the stream content to the output file
    with open(output_path, 'w') as f:
        f.write(stream.getvalue())

    logging.getLogger(__name__).info(f"Profiling report saved to {output_path}")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Profile smoothness analysis loop")
    parser.add_argument(
        "--primes",
        type=str,
        default="data/primes_1e9.csv",
        help="Path to primes CSV file"
    )
    parser.add_argument(
        "--x",
        type=int,
        default=10**6,
        help="Start of interval (default: 1,000,000)"
    )
    parser.add_argument(
        "--h",
        type=int,
        default=1000,
        help="Interval length (default: 1,000)"
    )
    parser.add_argument(
        "--y",
        type=int,
        default=100,
        help="Smoothness bound (default: 100)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/profiles/smoothness_baseline.txt",
        help="Output path for profiling report"
    )
    return parser.parse_args()

def main():
    """CLI entry point for profiling."""
    args = parse_args()
    
    # Setup logging
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        filename=os.path.join(log_dir, "profile_smoothness.log"),
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    logger.info(f"Starting profiling for x={args.x}, h={args.h}, y={args.y}")
    logger.info(f"Primes file: {args.primes}")
    logger.info(f"Output file: {args.output}")

    # Check if primes file exists
    if not os.path.exists(args.primes):
        logger.error(f"Primes file not found: {args.primes}")
        logger.error("Please run T012 and T013 to generate and validate the prime list first.")
        sys.exit(1)

    try:
        profile_smoothness_analysis(
            x=args.x,
            h=args.h,
            y=args.y,
            primes_path=args.primes,
            output_path=args.output
        )
        logger.info("Profiling completed successfully.")
    except Exception as e:
        logger.error(f"Profiling failed: {e}")
        raise

if __name__ == "__main__":
    main()