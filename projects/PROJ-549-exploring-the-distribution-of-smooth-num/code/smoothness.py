"""
code/smoothness.py: Factorization logic and smooth number counting.
"""
import argparse
import logging
import os
import sys
import time
from typing import List, Tuple, Optional, Dict, Any

def load_primes_from_csv(file_path: str) -> List[int]:
    """Load primes from CSV file (one per line)."""
    primes = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                primes.append(int(line))
    return primes

def is_y_smooth(n: int, y: int, primes: List[int]) -> bool:
    """
    Check if n is y-smooth (all prime factors ≤ y).
    Uses trial division against primes ≤ y.
    """
    if n < 2:
        return False
    if n == 1:
        return True

    # Filter primes ≤ y
    relevant_primes = [p for p in primes if p <= y]

    for p in relevant_primes:
        while n % p == 0:
            n //= p
        if n == 1:
            return True

    # If n > 1 after dividing by all primes ≤ y, then n has a prime factor > y
    return False

def count_smooth_in_interval(x: int, h: int, y: int, primes: List[int]) -> Tuple[int, int]:
    """
    Count y-smooth numbers in interval [x, x+h].
    Returns (count, total_numbers).
    """
    count = 0
    total = 0
    for n in range(x, x + h):
        total += 1
        if is_y_smooth(n, y, primes):
            count += 1
    return count, total

def run_smoothness_analysis(x: int, h: int, y: int, primes: List[int]) -> Dict[str, Any]:
    """
    Run smoothness analysis for a single interval.
    Returns a dictionary with results.
    """
    count, total = count_smooth_in_interval(x, h, y, primes)
    density = count / total if total > 0 else 0.0
    return {
        "x": x,
        "h": h,
        "y": y,
        "count": count,
        "total": total,
        "density": density
    }

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Smoothness analysis")
    parser.add_argument("--primes", type=str, default="data/primes_1e9.csv", help="Path to primes CSV")
    parser.add_argument("--x", type=int, default=10**6, help="Start of interval")
    parser.add_argument("--h", type=int, default=1000, help="Interval length")
    parser.add_argument("--y", type=int, default=100, help="Smoothness bound")
    return parser.parse_args()

def main():
    """CLI entry point for smoothness analysis."""
    args = parse_args()
    setup_logging("logs/smoothness.log")
    logger = logging.getLogger(__name__)

    logger.info(f"Loading primes from {args.primes}...")
    primes = load_primes_from_csv(args.primes)
    logger.info(f"Loaded {len(primes)} primes")

    result = run_smoothness_analysis(args.x, args.h, args.y, primes)
    logger.info(f"Result: {result}")

def setup_logging(log_file: str):
    """Setup logging."""
    import logging
    os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else '.', exist_ok=True)
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

if __name__ == "__main__":
    main()
