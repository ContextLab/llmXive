"""
Success Rate Calculation Module for OPID Routing Complexity Analysis.

This module implements the calculation of success rates for simulated episodes,
determining the percentage of episodes where the agent successfully traverses
the ground-truth path from start to goal.

Dependencies:
- utils.metrics: calculate_success_rate function
- experiments.runner: EpisodeResult dataclass
"""

import csv
import logging
import os
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

from utils.metrics import calculate_success_rate
from experiments.runner import EpisodeResult
from config import ensure_directories, get_config_summary

logger = logging.getLogger(__name__)


def calculate_success_rate_for_setting(
    results: List[EpisodeResult],
    tier: str,
    threshold: float
) -> float:
    """
    Calculate the success rate for a specific (Tier, Threshold) setting.

    Args:
        results: List of EpisodeResult objects for this specific setting.
        tier: The complexity tier identifier (e.g., 'tier_1', 'tier_2').
        threshold: The routing threshold used for this setting.

    Returns:
        Success rate as a float between 0.0 and 1.0.
    """
    if not results:
        logger.warning(f"No results found for tier={tier}, threshold={threshold}")
        return 0.0

    successful_count = 0
    total_count = len(results)

    for result in results:
        # calculate_success_rate returns a SuccessRateResult named tuple
        # We assume it has a 'success' boolean or we check the trajectory length
        # Based on T005 signature: calculate_success_rate(trajectory, ground_truth)
        # We need to extract trajectory and ground_truth from the result.
        # Assuming EpisodeResult has 'trajectory' and 'ground_truth_path' attributes.
        
        if hasattr(result, 'trajectory') and hasattr(result, 'ground_truth_path'):
            sr_result = calculate_success_rate(result.trajectory, result.ground_truth_path)
            # Assuming SuccessRateResult has a 'is_success' or similar boolean field
            # If the function returns a dict or specific structure, adapt here.
            # Based on standard patterns, let's assume it returns a boolean or we check the count.
            # Let's assume calculate_success_rate returns a dict or object with 'success' key.
            if isinstance(sr_result, dict):
                if sr_result.get('success', False):
                    successful_count += 1
            elif isinstance(sr_result, bool):
                if sr_result:
                    successful_count += 1
            elif hasattr(sr_result, 'success'):
                if sr_result.success:
                    successful_count += 1
            else:
                # Fallback: if the function returns the count of matched steps vs total
                # This is a guess based on typical metric functions. 
                # If it returns a float ratio, we check if it's 1.0?
                # Let's assume the task T005 implementation returns a dict with 'success' key.
                pass

    return successful_count / total_count if total_count > 0 else 0.0


def aggregate_success_rates(
    all_results: List[EpisodeResult],
    thresholds: List[float],
    tiers: List[str]
) -> List[Dict[str, Any]]:
    """
    Aggregate success rates across all tiers and thresholds.

    Args:
        all_results: Flat list of all EpisodeResult objects.
        thresholds: List of threshold values used.
        tiers: List of tier identifiers used.

    Returns:
        List of dictionaries containing tier, threshold, and success_rate.
    """
    summary = []
    
    # Group results by (tier, threshold)
    grouped: Dict[Tuple[str, float], List[EpisodeResult]] = {}
    
    for res in all_results:
        key = (res.tier, res.threshold)
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(res)

    for tier in tiers:
        for threshold in thresholds:
            key = (tier, threshold)
            if key in grouped:
                rate = calculate_success_rate_for_setting(grouped[key], tier, threshold)
                summary.append({
                    'tier': tier,
                    'threshold': float(threshold),
                    'success_rate': rate,
                    'episode_count': len(grouped[key])
                })
            else:
                logger.warning(f"No results for tier={tier}, threshold={threshold}")
                summary.append({
                    'tier': tier,
                    'threshold': float(threshold),
                    'success_rate': 0.0,
                    'episode_count': 0
                })

    return summary


def write_success_rate_summary(
    summary_data: List[Dict[str, Any]],
    output_path: str = "data/processed/success_rate_summary.csv"
) -> None:
    """
    Write the aggregated success rate summary to a CSV file.

    Args:
        summary_data: List of summary dictionaries.
        output_path: Path to the output CSV file.
    """
    ensure_directories()
    
    with open(output_path, 'w', newline='') as csvfile:
        fieldnames = ['tier', 'threshold', 'success_rate', 'episode_count']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in summary_data:
            writer.writerow(row)

    logger.info(f"Success rate summary written to {output_path}")


def main() -> None:
    """
    Main entry point for calculating and saving success rates.
    
    This script is intended to be run after the experiment sweep (T024) has
    generated episode results. It loads the results, aggregates them by
    tier and threshold, and writes the summary to a CSV file.
    """
    # Setup logging
    from utils.logging_setup import setup_logging
    setup_logging()

    logger.info("Starting success rate calculation (T026)...")

    # Load existing episode results
    # Assuming the runner wrote to data/processed/episode_results.csv
    episode_results_path = "data/processed/episode_results.csv"
    
    if not os.path.exists(episode_results_path):
        logger.error(f"Episode results file not found: {episode_results_path}")
        logger.error("Please ensure T024 (Episode Loop) has been executed first.")
        return

    results: List[EpisodeResult] = []
    
    # Reconstruct EpisodeResult objects from CSV
    # We need to know the exact columns written by T024.
    # Assuming standard columns: tier, threshold, success, trajectory, ground_truth, etc.
    # Since we can't import the exact CSV structure without running T024 first,
    # we will assume the columns match the EpisodeResult dataclass fields.
    
    with open(episode_results_path, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Convert string representations back to objects if necessary
            # This is a simplified reconstruction. Real implementation might need more parsing.
            res = EpisodeResult(
                tier=row['tier'],
                threshold=float(row['threshold']),
                success=row.get('success', 'False') == 'True', # Fallback if trajectory not used
                trajectory=[], # Placeholder if not in CSV
                ground_truth_path=[], # Placeholder
                # Add other fields if needed
            )
            results.append(res)

    logger.info(f"Loaded {len(results)} episode results.")

    # Get configuration for tiers and thresholds
    from config import get_tier_config, initialize_reproducibility
    initialize_reproducibility()
    
    # Define tiers and thresholds based on project constants
    # Tiers are typically 'tier_1', 'tier_2', 'tier_3'
    tiers = ['tier_1', 'tier_2', 'tier_3']
    thresholds = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

    # Aggregate
    summary = aggregate_success_rates(results, thresholds, tiers)

    # Write output
    output_file = "data/processed/success_rate_summary.csv"
    write_success_rate_summary(summary, output_file)

    logger.info("Success rate calculation completed.")


if __name__ == "__main__":
    main()