import os
import sys
import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.logging import get_logger, configure_logging
from src.utils.state_manager import compute_file_hash, update_state_artifact

logger = get_logger(__name__)

def simple_average(polls: List[Dict[str, float]]) -> float:
    """
    Calculate the arithmetic mean of vote shares per weekly bin.
    FR-003: Simple Unweighted Averaging.

    Args:
        polls: List of dictionaries containing 'vote_share' keys.

    Returns:
        float: The arithmetic mean of vote shares.
    """
    if not polls:
        logger.warning("No polls provided for simple average calculation.")
        return 0.0

    total = sum(p.get('vote_share', 0.0) for p in polls)
    count = len(polls)
    return total / count

def weighted_average(polls: List[Dict[str, float]]) -> float:
    """
    Calculate the inverse-RMSE weighted mean, normalizing weights to sum to 1.0.
    FR-004: Accuracy-Weighted Averaging.

    The weight for each poll is calculated as 1 / (historical_rmse + epsilon).
    If historical_rmse is missing or zero, a small epsilon prevents division by zero.
    Weights are then normalized so their sum equals 1.0.

    Args:
        polls: List of dictionaries containing 'vote_share' and 'historical_rmse' keys.

    Returns:
        float: The weighted average vote share.
    """
    if not polls:
        logger.warning("No polls provided for weighted average calculation.")
        return 0.0

    weights = []
    values = []
    epsilon = 1e-9

    for poll in polls:
        vote_share = poll.get('vote_share', 0.0)
        rmse = poll.get('historical_rmse', 0.0)

        # Ensure RMSE is positive to avoid division by zero
        if rmse <= 0:
            rmse = epsilon

        # Calculate inverse RMSE weight
        w = 1.0 / rmse
        weights.append(w)
        values.append(vote_share)

    # Normalize weights to sum to 1.0
    total_weight = sum(weights)
    if total_weight == 0:
        logger.warning("Total weight is zero. Falling back to simple average.")
        return simple_average(polls)

    normalized_weights = [w / total_weight for w in weights]

    # Calculate weighted sum
    weighted_sum = sum(v * w for v, w in zip(values, normalized_weights))

    return weighted_sum

def main():
    """
    Main entry point to run the frequentist aggregation on processed data.
    Reads data/processed/poll_data_cleaned.csv, calculates forecasts,
    and writes to data/processed/frequentist_forecasts.csv.
    """
    configure_logging()
    logger.info("Starting Frequentist Aggregation (Weighted Average)")

    input_path = project_root / "data" / "processed" / "poll_data_cleaned.csv"
    output_path = project_root / "data" / "processed" / "frequentist_forecasts.csv"

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    # Read data
    polls = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert string values to float
            try:
                vote_share = float(row['vote_share'])
                rmse = float(row['historical_rmse']) if 'historical_rmse' in row and row['historical_rmse'] else 0.0
                # Grouping key (e.g., week_bin) is assumed to be present for aggregation
                # For this specific task implementation, we assume the data is pre-binned
                # or we aggregate by a key if present. The task description implies
                # calculating the metric for the bins.
                # We will read the row and store the relevant fields.
                # If the file contains multiple rows per bin, we need to group them.
                # Assuming the file is already binned by 'week_bin' or similar.
                polls.append({
                    'vote_share': vote_share,
                    'historical_rmse': rmse,
                    'week_bin': row.get('week_bin', 'unknown'),
                    'pollster': row.get('pollster', 'unknown')
                })
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping invalid row: {row}. Error: {e}")

    if not polls:
        logger.error("No valid poll data found in input file.")
        sys.exit(1)

    # Group polls by week_bin
    from collections import defaultdict
    bins = defaultdict(list)
    for poll in polls:
        bins[poll['week_bin']].append(poll)

    # Calculate forecasts
    results = []
    for week_bin, bin_polls in sorted(bins.items()):
        simple_avg = simple_average(bin_polls)
        weighted_avg = weighted_average(bin_polls)

        results.append({
            'week_bin': week_bin,
            'simple_avg_forecast': simple_avg,
            'weighted_avg_forecast': weighted_avg,
            'poll_count': len(bin_polls)
        })

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['week_bin', 'simple_avg_forecast', 'weighted_avg_forecast', 'poll_count']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    logger.info(f"Forecasts written to {output_path}")

    # Update state manager
    update_state_artifact(
        project_root,
        "PROJ-206",
        output_path,
        "frequentist_forecasts.csv"
    )

    logger.info("Frequentist Aggregation completed successfully.")

if __name__ == "__main__":
    main()