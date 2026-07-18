"""
Module to generate the coverage_metrics.csv file from simulation results.
Implements T024: Create results/coverage_metrics.csv with headers
[phi, n, ordered_cov, shuffled_cov, diff, p_value].
"""
import json
import os
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import get_results_dir, ensure_directories
from metrics import mcnemar_test_logic

logger = logging.getLogger(__name__)


def load_results_from_log(log_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load simulation results from the JSON log file.
    
    Args:
        log_path: Path to the JSON log file. If None, uses default from config.
        
    Returns:
        List of dictionaries containing simulation results.
    """
    if log_path is None:
        results_dir = get_results_dir()
        log_path = str(results_dir / "simulation_logs.json")
    
    if not os.path.exists(log_path):
        raise FileNotFoundError(f"Simulation log not found at {log_path}")
    
    with open(log_path, 'r') as f:
        data = json.load(f)
    
    # The runner.py likely stores results as a list of trial objects
    # or a dict with a 'results' key. Handle both cases.
    if isinstance(data, dict):
        if 'results' in data:
            return data['results']
        elif 'trials' in data:
            return data['trials']
        else:
            # Assume the dict itself is a single result or list of results
            return [data] if not isinstance(data, list) else data
    elif isinstance(data, list):
        return data
    else:
        raise ValueError(f"Unexpected log format at {log_path}")


def aggregate_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Aggregate simulation results into rows for the CSV.
    
    Expects results to contain:
    - phi: float
    - n: int
    - ordered_coverage: float (or ordered_cov)
    - shuffled_coverage: float (or shuffled_cov)
    - ordered_covered: list of bool (for McNemar)
    - shuffled_covered: list of bool (for McNemar)
    
    Or pre-aggregated coverage values and raw counts for McNemar.
    
    Returns:
        List of dictionaries with keys: phi, n, ordered_cov, shuffled_cov, diff, p_value
    """
    aggregated = {}
    
    for trial in results:
        phi = trial.get('phi')
        n = trial.get('n')
        
        if phi is None or n is None:
            logger.warning(f"Skipping trial missing phi or n: {trial}")
            continue
        
        key = (phi, n)
        
        if key not in aggregated:
            aggregated[key] = {
                'phi': phi,
                'n': n,
                'ordered_covered': [],
                'shuffled_covered': []
            }
        
        # Handle different possible field names from runner.py
        # Try to extract coverage outcomes for McNemar's test
        if 'ordered_covered' in trial:
            aggregated[key]['ordered_covered'].extend(trial['ordered_covered'])
        elif 'ordered_coverage' in trial:
            # If only aggregate coverage is provided, we can't do McNemar
            # We'll store the aggregate and handle later
            aggregated[key]['ordered_cov'] = trial['ordered_coverage']
        
        if 'shuffled_covered' in trial:
            aggregated[key]['shuffled_covered'].extend(trial['shuffled_covered'])
        elif 'shuffled_coverage' in trial:
            aggregated[key]['shuffled_cov'] = trial['shuffled_coverage']
        
        # If we have per-trial outcomes, compute aggregate coverage
        if 'ordered_covered' in trial or 'shuffled_covered' in trial:
            if 'ordered_covered' in trial:
                oc = trial['ordered_covered']
                aggregated[key]['ordered_cov'] = sum(oc) / len(oc) if oc else 0.0
            if 'shuffled_covered' in trial:
                sc = trial['shuffled_covered']
                aggregated[key]['shuffled_cov'] = sum(sc) / len(sc) if sc else 0.0
    
    # Convert to list and compute derived metrics
    rows = []
    for key, data in aggregated.items():
        phi, n = key
        
        ordered_cov = data.get('ordered_cov', 0.0)
        shuffled_cov = data.get('shuffled_cov', 0.0)
        
        # Calculate difference
        diff = ordered_cov - shuffled_cov
        
        # Calculate p-value using McNemar's test if we have paired outcomes
        p_value = None
        if 'ordered_covered' in data and 'shuffled_covered' in data:
            ordered_list = data['ordered_covered']
            shuffled_list = data['shuffled_covered']
            
            if len(ordered_list) == len(shuffled_list) and len(ordered_list) > 0:
                # Build contingency table for McNemar's test
                # Table:
                #          Shuffled Covered
                #          Yes      No
                # Ordered  a        b
                # Yes      a        b
                # No       c        d
                
                a = sum(1 for o, s in zip(ordered_list, shuffled_list) if o and s)
                b = sum(1 for o, s in zip(ordered_list, shuffled_list) if o and not s)
                c = sum(1 for o, s in zip(ordered_list, shuffled_list) if not o and s)
                d = sum(1 for o, s in zip(ordered_list, shuffled_list) if not o and not s)
                
                try:
                    _, p_value = mcnemar_test_logic([[a, b], [c, d]])
                except Exception as e:
                    logger.warning(f"McNemar test failed for phi={phi}, n={n}: {e}")
                    p_value = None
            else:
                logger.warning(f"Mismatched list lengths for phi={phi}, n={n}")
        
        rows.append({
            'phi': phi,
            'n': n,
            'ordered_cov': ordered_cov,
            'shuffled_cov': shuffled_cov,
            'diff': diff,
            'p_value': p_value
        })
    
    # Sort by phi then n
    rows.sort(key=lambda x: (x['phi'], x['n']))
    
    return rows


def write_csv(rows: List[Dict[str, Any]], output_path: Optional[str] = None) -> str:
    """
    Write aggregated results to CSV file.
    
    Args:
        rows: List of dictionaries with keys: phi, n, ordered_cov, shuffled_cov, diff, p_value
        output_path: Path to output CSV. If None, uses default from config.
        
    Returns:
        Path to the written CSV file.
    """
    if output_path is None:
        results_dir = get_results_dir()
        output_path = str(results_dir / "coverage_metrics.csv")
    
    # Ensure directory exists
    ensure_directories()
    
    fieldnames = ['phi', 'n', 'ordered_cov', 'shuffled_cov', 'diff', 'p_value']
    
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in rows:
            # Handle None p_value
            row_copy = row.copy()
            if row_copy['p_value'] is None:
                row_copy['p_value'] = ''
            else:
                row_copy['p_value'] = f"{row_copy['p_value']:.6f}"
            
            writer.writerow(row_copy)
    
    logger.info(f"Wrote {len(rows)} rows to {output_path}")
    return output_path


def main():
    """Main entry point to generate the coverage metrics CSV."""
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Load results from simulation log
        results = load_results_from_log()
        
        if not results:
            logger.warning("No results found in simulation log.")
            return
        
        # Aggregate results
        aggregated = aggregate_results(results)
        
        if not aggregated:
            logger.warning("No aggregated results to write.")
            return
        
        # Write to CSV
        output_path = write_csv(aggregated)
        
        logger.info(f"Successfully generated {output_path}")
        
    except FileNotFoundError as e:
        logger.error(f"Simulation log not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating metrics CSV: {e}")
        raise


if __name__ == "__main__":
    main()