"""
Smoothness analysis module for computing y-smooth number densities.

This module implements the aggregation logic to compute density rho = count/h
and deviation ratio R = rho_obs / rho_Dickman(u) for random starting positions
across parameter grids.

Dependencies:
  - data/primes_1e9.csv (validated prime list from T012/T013)
  - code/dickman.py (Dickman function implementation from T004)
"""
import argparse
import csv
import json
import logging
import os
import sys
import random
from typing import List, Tuple, Optional, Dict, Any

import numpy as np

# Import from sibling modules
from dickman import rho, DickmanFunction
from config import GridConfig, load_config
from utils import setup_logging, set_deterministic_seed, generate_checksum

logger = logging.getLogger(__name__)

def load_primes_from_csv(filepath: str) -> List[int]:
    """Load primes from a CSV file (one prime per line)."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Prime file not found: {filepath}")
    
    primes = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                primes.append(int(line))
    
    logger.info(f"Loaded {len(primes)} primes from {filepath}")
    return primes

def is_y_smooth(n: int, y: int, primes: List[int]) -> bool:
    """
    Check if n is y-smooth (all prime factors <= y).
    
    Uses trial division against the precomputed primes list.
    """
    if n <= 1:
        return False
    
    temp = n
    for p in primes:
        if p > y:
            break
        while temp % p == 0:
            temp //= p
        if temp == 1:
            return True
    
    # If temp > 1 after dividing by all primes <= y, it has a prime factor > y
    return temp == 1

def count_smooth_in_interval(start: int, h: int, y: int, primes: List[int]) -> int:
    """
    Count y-smooth numbers in the interval [start, start + h).
    
    Args:
        start: Starting integer of the interval
        h: Length of the interval
        y: Smoothness bound
        primes: List of primes for factorization
    
    Returns:
        Count of y-smooth numbers in the interval
    """
    count = 0
    end = start + h
    
    for n in range(start, end):
        if is_y_smooth(n, y, primes):
            count += 1
    
    return count

def run_smoothness_analysis(x: int, h: int, y: int, primes: List[int], 
                            num_samples: int = 50, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Run smoothness analysis for a single configuration (x, h, y).
    
    Args:
        x: Base value (not directly used for sampling, but for context)
        h: Interval length
        y: Smoothness bound
        primes: List of primes
        num_samples: Number of random starting positions
        seed: Random seed for reproducibility
    
    Returns:
        List of results with density and deviation ratio
    """
    set_deterministic_seed(seed)
    results = []
    
    # Define valid range for random starting positions
    # Ensure the interval [start, start + h) stays within reasonable bounds
    # and doesn't exceed the prime list range (10^9)
    max_start = min(10**9 - h, 10**9 - 1)
    min_start = max(2, x)  # Start at least at x, but not below 2
    
    if min_start > max_start:
        logger.warning(f"Invalid range for x={x}, h={h}: min_start={min_start}, max_start={max_start}")
        return results
    
    for i in range(num_samples):
        start = random.randint(min_start, max_start)
        
        try:
            count = count_smooth_in_interval(start, h, y, primes)
            density = count / h if h > 0 else 0.0
            
            # Compute u = log(x) / log(y) for Dickman function
            # Use the midpoint of the interval for u calculation
            u = np.log(start + h/2) / np.log(y) if y > 1 else float('inf')
            
            # Get Dickman function value
            dickman_rho = rho(u) if u >= 0 else 0.0
            
            # Compute deviation ratio
            if dickman_rho > 0:
                deviation_ratio = density / dickman_rho
            else:
                deviation_ratio = float('nan') if density > 0 else 0.0
            
            results.append({
                'x': x,
                'y': y,
                'h': h,
                'start_offset': start - x,
                'start': start,
                'count': count,
                'density': density,
                'u': u,
                'dickman_rho': dickman_rho,
                'deviation_ratio': deviation_ratio
            })
            
        except Exception as e:
            logger.error(f"Error processing start={start}: {e}")
            continue
    
    return results

def run_grid_analysis(primes: List[int], grid_config: Dict[str, Any], 
                     num_samples: int = 50, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Run smoothness analysis across a grid of parameters.
    
    Args:
        primes: List of primes
        grid_config: Dictionary with 'x_values', 'y_values', 'h_values'
        num_samples: Number of samples per configuration
        seed: Random seed
    
    Returns:
        Combined list of all results
    """
    all_results = []
    
    x_values = grid_config.get('x_values', [10**6])
    y_values = grid_config.get('y_values', [100])
    h_values = grid_config.get('h_values', [1000])
    
    total_configs = len(x_values) * len(y_values) * len(h_values)
    logger.info(f"Running grid analysis: {total_configs} configurations")
    
    config_idx = 0
    for x in x_values:
        for y in y_values:
            for h in h_values:
                config_idx += 1
                logger.info(f"Processing config {config_idx}/{total_configs}: x={x}, y={y}, h={h}")
                
                results = run_smoothness_analysis(x, h, y, primes, num_samples, seed)
                all_results.extend(results)
    
    logger.info(f"Completed grid analysis: {len(all_results)} total samples")
    return all_results

def save_results_to_csv(results: List[Dict[str, Any]], output_path: str, source: str = 'default'):
    """
    Save results to a CSV file.
    
    Args:
        results: List of result dictionaries
        output_path: Path to output CSV
        source: Source identifier ('spec' or 'plan')
    """
    if not results:
        logger.warning("No results to save")
        # Still create the file with headers
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['x', 'y', 'h', 'start_offset', 'count', 'density', 'ratio', 'source'])
        return
    
    fieldnames = ['x', 'y', 'h', 'start_offset', 'count', 'density', 'ratio', 'source']
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            row = {
                'x': result['x'],
                'y': result['y'],
                'h': result['h'],
                'start_offset': result['start_offset'],
                'count': result['count'],
                'density': result['density'],
                'ratio': result['deviation_ratio'],
                'source': source
            }
            writer.writerow(row)
    
    logger.info(f"Saved {len(results)} results to {output_path}")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Compute y-smooth number densities across parameter grids.'
    )
    parser.add_argument(
        '--primes', 
        type=str, 
        default='data/primes_1e9.csv',
        help='Path to CSV file with primes (one per line)'
    )
    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='Path to grid configuration JSON file'
    )
    parser.add_argument(
        '--output-spec',
        type=str,
        default='data/density_measurements_spec.csv',
        help='Output path for Spec-defined grid results'
    )
    parser.add_argument(
        '--output-plan',
        type=str,
        default='data/density_measurements_plan.csv',
        help='Output path for Plan-defined grid results'
    )
    parser.add_argument(
        '--samples',
        type=int,
        default=50,
        help='Number of random starting positions per configuration'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )
    
    return parser.parse_args()

def main():
    """Main entry point for smoothness analysis."""
    args = parse_args()
    setup_logging(args.log_level)
    
    # Load primes
    logger.info(f"Loading primes from {args.primes}")
    try:
        primes = load_primes_from_csv(args.primes)
    except FileNotFoundError as e:
        logger.error(f"Failed to load primes: {e}")
        sys.exit(1)
    
    if len(primes) == 0:
        logger.error("No primes loaded. Cannot proceed.")
        sys.exit(1)
    
    # Define grids
    # Spec-defined grid: h in {x^0.1, x^0.3, x^0.5, x^0.7, x^0.9}
    spec_x_values = [10**6, 10**7, 10**8, 10**9]
    spec_y_values = [100, 1000, 10000]
    spec_h_values = {}
    for x in spec_x_values:
        spec_h_values[x] = [
            round(x**0.1),
            round(x**0.3),
            round(x**0.5),
            round(x**0.7),
            round(x**0.9)
        ]
    
    # Plan-defined grid: fixed h values
    plan_x_values = [10**6, 10**7, 10**8, 10**9]
    plan_y_values = [100, 1000, 10000]
    plan_h_values = [10**3, 10**4, 10**5, 10**6]
    
    # Run Spec grid analysis
    logger.info("Starting Spec-defined grid analysis")
    spec_results = []
    for x in spec_x_values:
        for y in spec_y_values:
            for h in spec_h_values[x]:
                if h <= 0:
                    continue
                results = run_smoothness_analysis(x, h, y, primes, args.samples, args.seed)
                spec_results.extend(results)
    
    # Save Spec results
    save_results_to_csv(spec_results, args.output_spec, source='spec')
    
    # Run Plan grid analysis
    logger.info("Starting Plan-defined grid analysis")
    plan_results = []
    for x in plan_x_values:
        for y in plan_y_values:
            for h in plan_h_values:
                if h <= 0:
                    continue
                results = run_smoothness_analysis(x, h, y, primes, args.samples, args.seed)
                plan_results.extend(results)
    
    # Save Plan results
    save_results_to_csv(plan_results, args.output_plan, source='plan')
    
    logger.info("Smoothness analysis completed successfully")
    logger.info(f"Spec grid: {len(spec_results)} samples -> {args.output_spec}")
    logger.info(f"Plan grid: {len(plan_results)} samples -> {args.output_plan}")

if __name__ == '__main__':
    main()