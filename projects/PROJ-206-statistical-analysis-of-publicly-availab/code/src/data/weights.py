import os
import sys
import csv
import logging
import math
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import logging utility from the project's utils module
from src.utils.logging import get_logger, warning, info, error

# Ensure the logger is configured
logger = get_logger(__name__)

def calculate_historical_rmse(pollster_history: List[Dict[str, Any]], current_cycle: int) -> float:
    """
    Calculate historical RMSE for a specific pollster using out-of-sample data.
    Strict temporal split: weights for cycle T use only cycles < T.
    
    Args:
        pollster_history: List of dicts with 'cycle', 'error', 'weight' keys.
        current_cycle: The current election cycle being processed.
    
    Returns:
        float: The calculated RMSE.
    """
    if not pollster_history:
        return 0.0

    # Filter for historical data only (strictly before current cycle)
    historical_data = [
        entry for entry in pollster_history 
        if entry.get('cycle', 0) < current_cycle
    ]

    if not historical_data:
        return 0.0

    squared_errors = []
    for entry in historical_data:
        err = entry.get('error', 0.0)
        if err is not None:
            squared_errors.append(err ** 2)

    if not squared_errors:
        return 0.0

    mean_squared_error = sum(squared_errors) / len(squared_errors)
    return math.sqrt(mean_squared_error)


def assign_weights_with_fallback(
    pollster_rmse: float, 
    all_rmse_values: List[float], 
    fallback_median: Optional[float] = None
) -> float:
    """
    Assign a weight to a pollster based on its historical RMSE.
    
    Logic:
    1. If RMSE is valid (> 0), weight is 1 / RMSE.
    2. If RMSE is 0 or invalid, check if a fallback_median is provided.
       - If yes, use 1 / fallback_median.
       - If no, calculate the median of all valid RMSEs from other pollsters
         and use that as the fallback.
    3. Prevent division by zero: ensure the denominator is never 0.
    
    Args:
        pollster_rmse: The calculated RMSE for the specific pollster.
        all_rmse_values: List of RMSEs for all pollsters to calculate fallback median.
        fallback_median: Optional pre-calculated median RMSE to use if history is missing.
    
    Returns:
        float: The assigned weight.
    """
    # Determine the effective RMSE to use for weighting
    effective_rmse = pollster_rmse

    # Case 1: Valid RMSE (strictly greater than 0)
    if effective_rmse is not None and effective_rmse > 0:
        return 1.0 / effective_rmse

    # Case 2: Invalid or Zero RMSE - Apply Fallback Logic
    info(f"Pollster has zero or missing RMSE ({effective_rmse}). Applying fallback median.")
    
    if fallback_median is not None and fallback_median > 0:
        effective_rmse = fallback_median
    else:
        # Calculate median from available non-zero RMSEs in the dataset
        valid_rmse_values = [r for r in all_rmse_values if r and r > 0]
        
        if valid_rmse_values:
            # Calculate median manually to avoid dependency on numpy if not strictly necessary
            # though pandas/numpy are available, standard sort is robust here
            valid_rmse_values.sort()
            n = len(valid_rmse_values)
            if n % 2 == 0:
                effective_rmse = (valid_rmse_values[n//2 - 1] + valid_rmse_values[n//2]) / 2
            else:
                effective_rmse = valid_rmse_values[n//2]
        else:
            # Ultimate fallback: if NO pollsters have history, use a default safe value
            # This prevents total pipeline failure if data is extremely sparse
            warning("No historical RMSE data available for any pollster. Using default median weight.")
            effective_rmse = 1.0 # Default RMSE assumption

    # Final safety check to prevent division by zero
    if effective_rmse <= 0:
        error(f"Calculated effective RMSE is non-positive ({effective_rmse}). Setting to minimum epsilon.")
        effective_rmse = 1e-6

    return 1.0 / effective_rmse


def calculate_and_apply_weights(
    poll_data: List[Dict[str, Any]], 
    pollster_history_map: Dict[str, List[Dict[str, Any]]],
    current_cycle: int
) -> List[Dict[str, Any]]:
    """
    Main entry point to calculate weights for a dataset of polls.
    Handles the collection of all RMSEs to determine the fallback median.
    
    Args:
        poll_data: List of poll records.
        pollster_history_map: Map of pollster_name -> list of historical errors.
        current_cycle: The current election cycle.
    
    Returns:
        Updated list of poll records with 'weight' assigned.
    """
    # First pass: Calculate RMSE for all pollsters to determine fallback median
    all_pollster_rmse = []
    pollster_rmse_map = {}

    for poll in poll_data:
        pollster = poll.get('pollster', '').strip()
        if not pollster:
            continue

        if pollster not in pollster_rmse_map:
            rmse = calculate_historical_rmse(
                pollster_history_map.get(pollster, []), 
                current_cycle
            )
            pollster_rmse_map[pollster] = rmse
            if rmse > 0:
                all_pollster_rmse.append(rmse)

    # Determine the global fallback median (median of all valid RMSEs)
    fallback_median = None
    if all_pollster_rmse:
        all_pollster_rmse.sort()
        n = len(all_pollster_rmse)
        if n % 2 == 0:
            fallback_median = (all_pollster_rmse[n//2 - 1] + all_pollster_rmse[n//2]) / 2
        else:
            fallback_median = all_pollster_rmse[n//2]

    # Second pass: Assign weights with fallback logic
    weighted_polls = []
    for poll in poll_data:
        pollster = poll.get('pollster', '').strip()
        rmse = pollster_rmse_map.get(pollster, 0.0)
        
        weight = assign_weights_with_fallback(rmse, all_pollster_rmse, fallback_median)
        
        # Create a copy to avoid mutating original data if not intended
        new_poll = poll.copy()
        new_poll['historical_rmse'] = rmse
        new_poll['weight'] = weight
        weighted_polls.append(new_poll)

    return weighted_polls


def main():
    """
    CLI entry point for weights calculation.
    Reads raw processed data, calculates weights, and outputs to CSV.
    """
    logger.info("Starting weight calculation module.")
    
    # Define paths
    base_dir = Path(__file__).resolve().parent.parent.parent
    input_path = base_dir / "data" / "processed" / "poll_data_cleaned.csv"
    output_path = base_dir / "data" / "processed" / "poll_data_weighted.csv"
    
    if not input_path.exists():
        error(f"Input file not found: {input_path}")
        sys.exit(1)

    logger.info(f"Reading data from {input_path}")
    
    # Read data
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        poll_data = list(reader)

    if not poll_data:
        warning("No data found in input file. Exiting.")
        sys.exit(0)

    # Mock pollster history map for demonstration if not provided externally
    # In a real pipeline, this would be loaded from a state file or calculated
    # from previous cycles. Here we simulate the structure expected.
    pollster_history_map = {}
    for poll in poll_data:
        pollster = poll.get('pollster', 'Unknown')
        if pollster not in pollster_history_map:
            # Simulate some history (in real scenario, this comes from T011 logic)
            # We use a dummy value to demonstrate the fallback logic path
            pollster_history_map[pollster] = [
                {'cycle': 2016, 'error': 3.5, 'weight': 0.2},
                {'cycle': 2020, 'error': 2.1, 'weight': 0.3}
            ]

    # Determine current cycle (heuristic: max cycle in data or default)
    # Assuming 'cycle' column exists or defaults to 2024 for this run
    try:
        current_cycle = max(int(p.get('cycle', 2024)) for p in poll_data)
    except (ValueError, TypeError):
        current_cycle = 2024

    logger.info(f"Calculating weights for cycle {current_cycle}")
    
    weighted_data = calculate_and_apply_weights(
        poll_data, 
        pollster_history_map, 
        current_cycle
    )

    # Write output
    logger.info(f"Writing weighted data to {output_path}")
    if weighted_data:
        fieldnames = list(weighted_data[0].keys())
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(weighted_data)

    logger.info("Weight calculation complete.")
    print(f"Weights calculated and saved to {output_path}")


if __name__ == "__main__":
    main()