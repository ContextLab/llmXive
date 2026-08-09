"""
Metrics calculation for CAP-ZPPO simulation.

Calculates Area Under the Convergence Curve (AUCC), final accuracy,
and average prompt length during mid-training cycles.
"""
import os
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path

from utils.logging import get_logger
from utils.seeds import get_seed

logger = get_logger(__name__)


def calculate_aucc(accuracies: List[float], cycles: Optional[List[int]] = None) -> float:
    """
    Calculate the Area Under the Convergence Curve (AUCC) using the trapezoidal rule.
    
    Args:
        accuracies: List of accuracy values per cycle.
        cycles: Optional list of cycle indices. If None, assumes [0, 1, 2, ...].
    
    Returns:
        The calculated AUCC value.
    """
    if not accuracies:
        logger.warning("Empty accuracy list provided to calculate_aucc. Returning 0.0.")
        return 0.0

    if cycles is None:
        cycles = list(range(len(accuracies)))
    
    if len(accuracies) != len(cycles):
        raise ValueError(f"Length mismatch: accuracies ({len(accuracies)}) vs cycles ({len(cycles)})")
    
    if len(accuracies) < 2:
        # If only one point, area is 0 (or could be considered a single point with 0 width)
        return 0.0

    # Normalize cycles to 0..1 range for standard AUCC interpretation if needed,
    # but typically raw trapezoidal integration is fine for comparison.
    # Here we use raw values.
    x = np.array(cycles, dtype=float)
    y = np.array(accuracies, dtype=float)

    # Trapezoidal integration
    area = np.trapz(y, x)
    
    logger.info(f"AUCC calculated: {area:.6f} from {len(accuracies)} points.")
    return float(area)


def calculate_final_accuracy(accuracies: List[float]) -> float:
    """
    Calculate the final accuracy from the last cycle.
    
    Args:
        accuracies: List of accuracy values per cycle.
    
    Returns:
        The accuracy of the last cycle.
    """
    if not accuracies:
        logger.warning("Empty accuracy list provided to calculate_final_accuracy. Returning 0.0.")
        return 0.0
    
    final_acc = accuracies[-1]
    logger.info(f"Final accuracy: {final_acc:.6f}")
    return float(final_acc)


def calculate_average_mid_training_prompt_length(
    prompt_lengths: List[int], 
    total_cycles: int, 
    mid_start_ratio: float = 0.25, 
    mid_end_ratio: float = 0.75
) -> float:
    """
    Calculate the average prompt length during the mid-training phase.
    
    The mid-training phase is defined as the period between `mid_start_ratio` 
    and `mid_end_ratio` of the total training cycles.
    
    Args:
        prompt_lengths: List of prompt lengths per cycle.
        total_cycles: Total number of training cycles.
        mid_start_ratio: Start of mid-training as a fraction of total cycles (0.0-1.0).
        mid_end_ratio: End of mid-training as a fraction of total cycles (0.0-1.0).
    
    Returns:
        The average prompt length in the mid-training window.
    """
    if not prompt_lengths:
        logger.warning("Empty prompt_lengths list. Returning 0.0.")
        return 0.0

    if len(prompt_lengths) != total_cycles:
        # Handle case where prompt_lengths might be shorter than expected total_cycles
        # or if total_cycles is just a parameter and we use len(prompt_lengths)
        logger.warning(f"Length mismatch: prompt_lengths ({len(prompt_lengths)}) vs total_cycles ({total_cycles}). Using len(prompt_lengths).")
        total_cycles = len(prompt_lengths)

    start_idx = int(total_cycles * mid_start_ratio)
    end_idx = int(total_cycles * mid_end_ratio)
    
    # Ensure bounds
    start_idx = max(0, start_idx)
    end_idx = max(start_idx + 1, min(total_cycles, end_idx))
    
    mid_lengths = prompt_lengths[start_idx:end_idx]
    
    if not mid_lengths:
        logger.warning("No prompt lengths found in mid-training window. Returning 0.0.")
        return 0.0

    avg_length = float(np.mean(mid_lengths))
    logger.info(f"Average prompt length (cycles {start_idx} to {end_idx}): {avg_length:.2f}")
    return avg_length


def calculate_metrics(
    accuracies: List[float],
    prompt_lengths: Optional[List[int]] = None,
    total_cycles: Optional[int] = None
) -> Dict[str, float]:
    """
    Calculate all relevant metrics for a simulation run.
    
    Args:
        accuracies: List of accuracy values per cycle.
        prompt_lengths: Optional list of prompt lengths per cycle (for CAP runs).
        total_cycles: Optional total cycle count (defaults to len(accuracies)).
    
    Returns:
        Dictionary containing:
            - 'aucc': Area Under Convergence Curve
            - 'final_accuracy': Accuracy at the last cycle
            - 'avg_mid_prompt_length': Average prompt length in mid-training (if prompt_lengths provided)
    """
    metrics = {}
    
    # AUCC
    metrics['aucc'] = calculate_aucc(accuracies)
    
    # Final Accuracy
    metrics['final_accuracy'] = calculate_final_accuracy(accuracies)
    
    # Mid-training Prompt Length (only if data provided)
    if prompt_lengths is not None:
        if total_cycles is None:
            total_cycles = len(accuracies)
        metrics['avg_mid_prompt_length'] = calculate_average_mid_training_prompt_length(
            prompt_lengths, total_cycles
        )
    else:
        metrics['avg_mid_prompt_length'] = None
        logger.info("Prompt lengths not provided; skipping mid-training prompt length calculation.")
    
    return metrics


def save_metrics_to_csv(
    metrics: Dict[str, float],
    output_path: str,
    run_metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Save metrics to a CSV file.
    
    Args:
        metrics: Dictionary of metric names to values.
        output_path: Path to the output CSV file.
        run_metadata: Optional dictionary of metadata to include as columns.
    """
    import csv
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Combine metadata and metrics
    row_data = {}
    if run_metadata:
        row_data.update(run_metadata)
    row_data.update(metrics)
    
    # Determine headers (metadata keys first, then metric keys)
    headers = list(row_data.keys())
    
    with open(output_path, mode='w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerow(row_data)
    
    logger.info(f"Metrics saved to {output_path}")


def load_metrics_from_csv(input_path: str) -> List[Dict[str, Any]]:
    """
    Load metrics from a CSV file.
    
    Args:
        input_path: Path to the input CSV file.
    
    Returns:
        List of dictionaries, one per row.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Metrics file not found: {input_path}")
    
    with open(input_path, mode='r') as f:
        reader = csv.DictReader(f)
        return list(reader)