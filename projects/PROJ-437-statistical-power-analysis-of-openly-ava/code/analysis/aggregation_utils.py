"""
Aggregation utilities for power analysis results.

This module provides functions to aggregate power curve results across
sample sizes, paradigms, and smoothing kernels into a unified JSON format.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

def aggregate_power_results(
    results_list: List[Dict[str, Any]],
    output_path: Union[str, Path]
) -> Dict[str, Any]:
    """
    Aggregate power curve results from multiple runs into a single JSON file.
    
    This function takes a list of power curve results (each containing sample sizes
    and empirical replication rates) and aggregates them into a structured format
    with `sample_sizes_tested` and `empirical_rates` arrays.
    
    Args:
        results_list: List of dictionaries, each containing:
            - 'sample_sizes': List of int
            - 'empirical_rates': List of float (0-1)
            - 'paradigm': str (optional)
            - 'kernel': str (optional)
        output_path: Path to write the aggregated JSON file.
    
    Returns:
        The aggregated dictionary that was written to disk.
    
    Raises:
        ValueError: If results_list is empty or contains invalid data.
        IOError: If unable to write to output_path.
    """
    if not results_list:
        raise ValueError("results_list cannot be empty")
    
    aggregated = {
        "metadata": {
            "num_sources": len(results_list),
            "aggregation_timestamp": None  # Will be set by caller if needed
        },
        "sample_sizes_tested": [],
        "empirical_rates": [],
        "paradigm_breakdown": {},
        "kernel_breakdown": {}
    }
    
    # Track unique sample sizes across all runs
    all_sample_sizes = set()
    for result in results_list:
        if "sample_sizes" not in result:
            raise ValueError(f"Missing 'sample_sizes' in result: {result}")
        if "empirical_rates" not in result:
            raise ValueError(f"Missing 'empirical_rates' in result: {result}")
        if len(result["sample_sizes"]) != len(result["empirical_rates"]):
            raise ValueError(
                f"Sample sizes and empirical rates length mismatch in result: {result}"
            )
        all_sample_sizes.update(result["sample_sizes"])
    
    sorted_sample_sizes = sorted(all_sample_sizes)
    aggregated["sample_sizes_tested"] = sorted_sample_sizes
    
    # Aggregate empirical rates by sample size
    rate_accumulator = {size: [] for size in sorted_sample_sizes}
    
    for idx, result in enumerate(results_list):
        paradigm = result.get("paradigm", "unknown")
        kernel = result.get("kernel", "unknown")
        
        # Track paradigm-specific rates
        if paradigm not in aggregated["paradigm_breakdown"]:
            aggregated["paradigm_breakdown"][paradigm] = {
                "sample_sizes_tested": [],
                "empirical_rates": []
            }
        
        # Track kernel-specific rates
        if kernel not in aggregated["kernel_breakdown"]:
            aggregated["kernel_breakdown"][kernel] = {
                "sample_sizes_tested": [],
                "empirical_rates": []
            }
        
        for size, rate in zip(result["sample_sizes"], result["empirical_rates"]):
            rate_accumulator[size].append(rate)
            
            # Add to paradigm breakdown
            if size not in aggregated["paradigm_breakdown"][paradigm]["sample_sizes_tested"]:
                aggregated["paradigm_breakdown"][paradigm]["sample_sizes_tested"].append(size)
                # Find corresponding index and rate
                size_idx = result["sample_sizes"].index(size)
                aggregated["paradigm_breakdown"][paradigm]["empirical_rates"].append(
                    result["empirical_rates"][size_idx]
                )
            
            # Add to kernel breakdown
            if size not in aggregated["kernel_breakdown"][kernel]["sample_sizes_tested"]:
                aggregated["kernel_breakdown"][kernel]["sample_sizes_tested"].append(size)
                size_idx = result["sample_sizes"].index(size)
                aggregated["kernel_breakdown"][kernel]["empirical_rates"].append(
                    result["empirical_rates"][size_idx]
                )
    
    # Compute mean empirical rate for each sample size across all runs
    aggregated["empirical_rates"] = [
        sum(rates) / len(rates) if rates else 0.0
        for rates in [rate_accumulator[size] for size in sorted_sample_sizes]
    ]
    
    # Sort paradigm and kernel breakdowns by sample size
    for paradigm in aggregated["paradigm_breakdown"]:
        sizes = aggregated["paradigm_breakdown"][paradigm]["sample_sizes_tested"]
        rates = aggregated["paradigm_breakdown"][paradigm]["empirical_rates"]
        sorted_pairs = sorted(zip(sizes, rates))
        aggregated["paradigm_breakdown"][paradigm]["sample_sizes_tested"] = [
            s for s, _ in sorted_pairs
        ]
        aggregated["paradigm_breakdown"][paradigm]["empirical_rates"] = [
            r for _, r in sorted_pairs
        ]
    
    for kernel in aggregated["kernel_breakdown"]:
        sizes = aggregated["kernel_breakdown"][kernel]["sample_sizes_tested"]
        rates = aggregated["kernel_breakdown"][kernel]["empirical_rates"]
        sorted_pairs = sorted(zip(sizes, rates))
        aggregated["kernel_breakdown"][kernel]["sample_sizes_tested"] = [
            s for s, _ in sorted_pairs
        ]
        aggregated["kernel_breakdown"][kernel]["empirical_rates"] = [
            r for _, r in sorted_pairs
        ]
    
    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to JSON
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(aggregated, f, indent=2)
        logger.info(f"Aggregated power curves written to {output_path}")
    except IOError as e:
        logger.error(f"Failed to write aggregated results to {output_path}: {e}")
        raise
    
    return aggregated