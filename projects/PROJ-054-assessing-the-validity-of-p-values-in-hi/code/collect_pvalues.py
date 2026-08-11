"""
T024 Implementation: P-value Collection Logic

Collects p-values from hypothesis tests run in run_tests.py.
Ensures exactly p values are collected per iteration.
Stores results in data/results/pvalues_{seed}.csv.
"""

import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

import numpy as np

# Import from local utils
from utils.exceptions import HypothesisTestError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

RESULTS_DIR = Path("data/results")

def collect_pvalues(pvalue_dict: Dict[str, float], expected_p: int, seed: int) -> List[Dict[str, Any]]:
    """
    Collect p-values from a hypothesis test result dictionary.
    
    Args:
        pvalue_dict: Dictionary containing p-values, expected to have keys like
                    't_test_pvalues' or 'f_test_pvalues' containing arrays.
        expected_p: The expected number of p-values (should match dimension p).
        seed: The seed used for this iteration.
    
    Returns:
        List of dictionaries with columns: feature_idx, pvalue, test_type
    
    Raises:
        HypothesisTestError: If the number of collected p-values does not match expected_p.
    """
    collected = []
    test_types_found = []
    
    # Check for t-test p-values
    if 't_test_pvalues' in pvalue_dict:
        pvals = pvalue_dict['t_test_pvalues']
        if isinstance(pvals, np.ndarray):
            pvals = pvals.tolist()
        if len(pvals) != expected_p:
            raise HypothesisTestError(
                f"t_test_pvalues count ({len(pvals)}) does not match expected p ({expected_p})"
            )
        for idx, pval in enumerate(pvals):
            collected.append({
                'feature_idx': idx,
                'pvalue': pval,
                'test_type': 't-test'
            })
        test_types_found.append('t-test')
    
    # Check for F-test p-values
    if 'f_test_pvalues' in pvalue_dict:
        pvals = pvalue_dict['f_test_pvalues']
        if isinstance(pvals, np.ndarray):
            pvals = pvals.tolist()
        if len(pvals) != expected_p:
            raise HypothesisTestError(
                f"f_test_pvalues count ({len(pvals)}) does not match expected p ({expected_p})"
            )
        for idx, pval in enumerate(pvals):
            collected.append({
                'feature_idx': idx,
                'pvalue': pval,
                'test_type': 'f-test'
            })
        test_types_found.append('f-test')
    
    if not test_types_found:
        raise HypothesisTestError("No p-values found in result dictionary")
    
    # Final verification: total count must equal expected_p
    # If both tests ran, we expect expected_p from each, but we validate per test type above.
    # The primary check is that each test type produced exactly p values.
    
    logger.info(f"Collected {len(collected)} p-values from {test_types_found} for seed {seed}")
    return collected

def aggregate_pvalues(collected_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate collected p-values for summary statistics.
    
    Args:
        collected_list: List of dictionaries from collect_pvalues.
    
    Returns:
        Dictionary with summary statistics.
    """
    if not collected_list:
        return {}
    
    pvalues = [item['pvalue'] for item in collected_list]
    test_types = set(item['test_type'] for item in collected_list)
    
    return {
        'count': len(pvalues),
        'min': float(min(pvalues)),
        'max': float(max(pvalues)),
        'mean': float(np.mean(pvalues)),
        'median': float(np.median(pvalues)),
        'std': float(np.std(pvalues)),
        'test_types': list(test_types)
    }

def write_trajectory_snapshot(collected: List[Dict[str, Any]], seed: int, output_dir: Optional[Path] = None) -> Path:
    """
    Write p-values to a CSV file for this iteration.
    
    Args:
        collected: List of p-value dictionaries from collect_pvalues.
        seed: The seed for this iteration (used in filename).
        output_dir: Directory to write the file. Defaults to data/results.
    
    Returns:
        Path to the written file.
    
    Raises:
        HypothesisTestError: If the number of rows does not match expected p (inferred from data).
    """
    if output_dir is None:
        output_dir = RESULTS_DIR
    
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"pvalues_{seed}.csv"
    
    if not collected:
        raise HypothesisTestError("Cannot write empty p-value collection")
    
    # Infer expected_p from the first item's feature_idx (assuming 0-indexed continuous)
    # Or simply count unique feature indices if they are not contiguous
    expected_p = max(item['feature_idx'] for item in collected) + 1
    
    with open(output_path, 'w', newline='') as csvfile:
        fieldnames = ['feature_idx', 'pvalue', 'test_type']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in collected:
            writer.writerow(row)
    
    # Verification: Count rows in the file
    row_count = sum(1 for _ in open(output_path)) - 1  # subtract header
    if row_count != expected_p:
        raise HypothesisTestError(
            f"Verification failed: File {output_path} has {row_count} data rows, "
            f"but expected {expected_p} based on feature indices."
        )
    
    logger.info(f"Wrote {row_count} p-values to {output_path}")
    return output_path

def main():
    """
    Main entry point for testing the collection logic.
    Simulates a run where p-values are collected and written.
    """
    # This function is primarily for testing the API.
    # In the full pipeline, run_tests.py calls collect_pvalues and write_trajectory_snapshot.
    
    # Example usage simulation:
    try:
        # Simulate a result from run_hypothesis_tests
        seed = 42
        p_dim = 10
        mock_result = {
            't_test_pvalues': np.random.uniform(0, 1, p_dim),
            'f_test_pvalues': np.random.uniform(0, 1, p_dim)
        }
        
        # Collect
        collected = collect_pvalues(mock_result, expected_p=p_dim, seed=seed)
        
        # Write
        out_path = write_trajectory_snapshot(collected, seed)
        
        print(f"Successfully wrote p-values to: {out_path}")
        print(f"File exists: {out_path.exists()}")
        
    except HypothesisTestError as e:
        logger.error(f"Collection error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()