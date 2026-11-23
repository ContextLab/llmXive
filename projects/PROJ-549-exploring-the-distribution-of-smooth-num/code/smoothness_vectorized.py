"""
Vectorized Smooth Number Factorization Module (T032b)

Implements high-performance smoothness checking using NumPy broadcasting
to evaluate entire intervals at once, replacing the scalar loop in smoothness.py.
"""
import argparse
import logging
import os
import sys
import time
from typing import List, Tuple, Optional, Dict, Any

import numpy as np

# Import existing utilities from sibling modules
from config import load_config
from utils import setup_logging


def load_primes_as_array(primes_path: str) -> np.ndarray:
    """
    Load primes from CSV into a NumPy array for vectorized operations.
    
    Args:
        primes_path: Path to the CSV file containing primes (one per line or single column).
        
    Returns:
        np.ndarray: Array of primes.
    """
    if not os.path.exists(primes_path):
        raise FileNotFoundError(f"Prime file not found: {primes_path}")
    
    # Read all lines, strip whitespace, convert to int
    # Assuming one prime per line based on T012 output format
    with open(primes_path, 'r') as f:
        # Use numpy's loadtxt for efficiency, skipping any header if present
        # If the file is strictly one integer per line, this works perfectly.
        try:
            primes = np.loadtxt(primes_path, dtype=np.int64)
        except ValueError:
            # Fallback for potential whitespace issues
            lines = [line.strip() for line in f if line.strip()]
            primes = np.array([int(x) for x in lines], dtype=np.int64)
    
    return primes


def is_y_smooth_vectorized(intervals: np.ndarray, primes: np.ndarray, y: int) -> np.ndarray:
    """
    Determine if numbers in 'intervals' are y-smooth using vectorized broadcasting.
    
    A number n is y-smooth if all its prime factors are <= y.
    We achieve this by:
    1. Filtering primes <= y.
    2. For each number, repeatedly dividing by these primes.
    3. Checking if the remaining value is 1.
    
    Note: This implementation uses a loop over primes but vectorizes the division
    across the entire interval array, which is significantly faster than looping
    over intervals in pure Python.
    
    Args:
        intervals: 1D numpy array of integers to check.
        primes: 1D numpy array of all known primes.
        y: Smoothness bound.
        
    Returns:
        1D boolean array where True indicates the number is y-smooth.
    """
    if len(intervals) == 0:
        return np.array([], dtype=bool)
    
    # Filter primes up to y
    relevant_primes = primes[primes <= y]
    
    if len(relevant_primes) == 0:
        # If no primes <= y, only 1 is smooth (if present), others are not
        # But typically intervals start > 1.
        return intervals == 1
    
    # Create a working copy of the intervals for division
    # We use int64 to prevent overflow during intermediate steps if any,
    # though input is already int64.
    remaining = intervals.copy()
    
    # Vectorized division loop
    # For each prime, divide out all occurrences from all numbers in parallel
    for p in relevant_primes:
        # While there are numbers divisible by p, divide them
        # We do this in a loop because we need to divide out ALL factors of p
        # However, for large primes, the number of divisions is small.
        # Optimization: We can do log_p(max_val) iterations, but a while loop 
        # checking mask is usually faster in NumPy than fixed iterations.
        mask = (remaining % p == 0)
        while mask.any():
            remaining[mask] //= p
            mask = (remaining % p == 0)
    
    # A number is y-smooth if all its prime factors were <= y.
    # After dividing out all factors <= y, the remainder should be 1.
    return remaining == 1


def count_smooth_in_interval_vectorized(
    start: int, 
    length: int, 
    primes: np.ndarray, 
    y: int
) -> int:
    """
    Count y-smooth numbers in the interval [start, start + length).
    
    Args:
        start: Start of the interval.
        length: Length of the interval.
        primes: Array of all primes.
        y: Smoothness bound.
        
    Returns:
        Count of y-smooth numbers.
    """
    if length <= 0:
        return 0
    
    # Generate the interval array
    # Using np.arange to create the range [start, start + length)
    intervals = np.arange(start, start + length, dtype=np.int64)
    
    # Perform vectorized smoothness check
    smooth_mask = is_y_smooth_vectorized(intervals, primes, y)
    
    return int(np.sum(smooth_mask))


def run_vectorized_analysis(
    primes_path: str, 
    output_path: str,
    x_start: int,
    x_end: int,
    y: int,
    step: int
) -> Dict[str, Any]:
    """
    Run smoothness analysis over a range of x values using the vectorized method.
    
    Args:
        primes_path: Path to the primes CSV.
        output_path: Path to save results.
        x_start: Starting x value.
        x_end: Ending x value (exclusive).
        y: Smoothness bound.
        step: Step size between x values.
        
    Returns:
        Dictionary with results summary.
    """
    logging.info(f"Loading primes from {primes_path}...")
    primes = load_primes_as_array(primes_path)
    logging.info(f"Loaded {len(primes)} primes.")
    
    results = []
    start_time = time.time()
    
    current_x = x_start
    count = 0
    while current_x < x_end:
        count += 1
        smooth_count = count_smooth_in_interval_vectorized(
            current_x, 
            1000, # Fixed interval length for benchmarking
            primes, 
            y
        )
        results.append({
            "x": current_x,
            "y_smooth_count": smooth_count,
            "density": smooth_count / 1000.0
        })
        current_x += step
        
        # Progress logging
        if count % 100 == 0:
            logging.info(f"Processed {count} intervals (x={current_x})")
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    # Save results
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w') as f:
        f.write("x,y_smooth_count,density\n")
        for r in results:
            f.write(f"{r['x']},{r['y_smooth_count']},{r['density']:.6f}\n")
    
    return {
        "total_intervals": count,
        "elapsed_seconds": elapsed,
        "output_path": output_path,
        "method": "vectorized_numpy_broadcasting"
    }


def main():
    """CLI entry point for vectorized smoothness analysis."""
    parser = argparse.ArgumentParser(description="Vectorized Smooth Number Analysis (T032b)")
    parser.add_argument("--primes", type=str, default="data/primes_1e9.csv", help="Path to primes CSV")
    parser.add_argument("--output", type=str, default="data/vectorized_results.csv", help="Output CSV path")
    parser.add_argument("--x-start", type=int, default=1000000, help="Start x")
    parser.add_argument("--x-end", type=int, default=10000000, help="End x")
    parser.add_argument("--y", type=int, default=100, help="Smoothness bound y")
    parser.add_argument("--step", type=int, default=10000, help="Step size between x")
    
    args = parser.parse_args()
    
    setup_logging(level=logging.INFO)
    
    try:
        results = run_vectorized_analysis(
            args.primes,
            args.output,
            args.x_start,
            args.x_end,
            args.y,
            args.step
        )
        logging.info(f"Analysis complete. Results saved to {results['output_path']}")
        logging.info(f"Total intervals: {results['total_intervals']}, Time: {results['elapsed_seconds']:.2f}s")
    except Exception as e:
        logging.error(f"Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
