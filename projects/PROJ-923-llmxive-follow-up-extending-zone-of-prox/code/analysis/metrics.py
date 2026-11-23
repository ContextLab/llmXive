"""
Metrics calculation module for ZPPO and CAP simulations.

This module provides functions to calculate key performance metrics including:
- Area Under the Convergence Curve (AUCC)
- Final accuracy
- Average prompt length (specifically for CAP)
- Aggregated metrics from simulation logs
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import json

from utils.logging import get_logger, info, debug, warning
from utils.seeds import get_rng

logger = get_logger(__name__)


def calculate_aucc(accuracies: List[float], cycles: Optional[List[int]] = None) -> float:
    """
    Calculate the Area Under the Convergence Curve (AUCC) using the trapezoidal rule.

    Args:
        accuracies: List of accuracy values per cycle.
        cycles: Optional list of cycle indices. If None, assumes sequential 0..N-1.

    Returns:
        AUCC value (float).
    """
    if not accuracies:
        warning("Empty accuracies list provided to calculate_aucc. Returning 0.0.")
        return 0.0

    y = np.array(accuracies)
    if cycles is None:
        x = np.arange(len(y))
    else:
        x = np.array(cycles)

    if len(x) != len(y):
        raise ValueError(f"Length mismatch: cycles ({len(x)}) != accuracies ({len(y)})")

    # Trapezoidal integration
    aucc = np.trapz(y, x)
    
    # Normalize by the range of x to get an average accuracy-like metric if needed,
    # but typically AUCC is the raw integral. We return the raw integral here.
    # If normalization is required by downstream, it can be done there.
    # However, for comparison, sometimes normalized AUCC (mean accuracy) is preferred.
    # Let's return the raw integral as per standard definition, but note that
    # if cycles are 0..N, the max possible area is N * 1.0.
    
    debug(f"AUCC calculated: {aucc:.4f} for {len(accuracies)} cycles.")
    return float(aucc)


def calculate_final_accuracy(accuracies: List[float]) -> float:
    """
    Calculate the final accuracy (last value in the sequence).

    Args:
        accuracies: List of accuracy values per cycle.

    Returns:
        Final accuracy value (float).
    """
    if not accuracies:
        warning("Empty accuracies list provided to calculate_final_accuracy. Returning 0.0.")
        return 0.0

    final_acc = float(accuracies[-1])
    debug(f"Final accuracy calculated: {final_acc:.4f}")
    return final_acc


def calculate_average_prompt_length(prompt_lengths: List[int]) -> float:
    """
    Calculate the average prompt length.

    For CAP-ZPPO, this is specifically the average number of negative candidates
    included in the prompt across all cycles.

    Args:
        prompt_lengths: List of prompt lengths (number of candidates) per cycle.

    Returns:
        Average prompt length (float).
    """
    if not prompt_lengths:
        warning("Empty prompt_lengths list provided to calculate_average_prompt_length. Returning 0.0.")
        return 0.0

    avg_len = float(np.mean(prompt_lengths))
    debug(f"Average prompt length calculated: {avg_len:.2f}")
    return avg_len


def calculate_metrics_from_log(
    log_data: List[Dict[str, Any]],
    metric_type: str = "cap"
) -> Dict[str, float]:
    """
    Calculate metrics from a simulation log (list of cycle records).

    Args:
        log_data: List of dictionaries, each representing a cycle's results.
                Expected keys: 'cycle', 'accuracy', 'prompt_length' (for CAP).
        metric_type: Type of simulation ('cap' or 'baseline').
                    'baseline' ignores prompt_length as it's constant.

    Returns:
        Dictionary containing calculated metrics.
    """
    if not log_data:
        raise ValueError("Empty log_data provided to calculate_metrics_from_log.")

    accuracies = []
    prompt_lengths = []
    cycles = []

    for record in log_data:
        cycles.append(record.get('cycle', 0))
        accuracies.append(record.get('accuracy', 0.0))
        
        if metric_type == "cap":
            # For CAP, we expect prompt_length to be present
            pl = record.get('prompt_length')
            if pl is None:
                warning(f"Missing 'prompt_length' in cycle {record.get('cycle')}. Using 0.")
                pl = 0
            prompt_lengths.append(pl)
        else:
            # For baseline, prompt length is conceptually constant or not tracked per cycle
            # We skip adding to prompt_lengths list to avoid confusion
            pass

    metrics = {
        "aucc": calculate_aucc(accuracies, cycles),
        "final_accuracy": calculate_final_accuracy(accuracies)
    }

    if metric_type == "cap" and prompt_lengths:
        metrics["average_prompt_length"] = calculate_average_prompt_length(prompt_lengths)
    else:
        # Baseline or missing prompt lengths
        metrics["average_prompt_length"] = None

    return metrics


def save_metrics_to_csv(metrics: Dict[str, Any], output_path: str) -> None:
    """
    Save metrics dictionary to a CSV file.

    Args:
        metrics: Dictionary of metrics to save.
        output_path: Path to the output CSV file.
    """
    output_path = Path(output_path)
    ensure_directory(output_path.parent)

    # Flatten nested metrics if any, though we expect a flat dict here
    df = pd.DataFrame([metrics])
    df.to_csv(output_path, index=False)
    info(f"Metrics saved to {output_path}")


def ensure_directory(dir_path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    if not dir_path.exists():
        dir_path.mkdir(parents=True, exist_ok=True)
        debug(f"Created directory: {dir_path}")


def calculate_baseline_metrics(log_path: str) -> Dict[str, Any]:
    """
    Calculate metrics for a baseline (static NCQ) simulation.

    Args:
        log_path: Path to the baseline simulation log file (JSON).

    Returns:
        Dictionary containing AUCC, final_accuracy.
    """
    log_path = Path(log_path)
    if not log_path.exists():
        raise FileNotFoundError(f"Baseline log file not found: {log_path}")

    with open(log_path, 'r') as f:
        log_data = json.load(f)

    metrics = calculate_metrics_from_log(log_data, metric_type="baseline")
    info(f"Baseline metrics calculated: {metrics}")
    return metrics


def calculate_cap_metrics(log_path: str) -> Dict[str, Any]:
    """
    Calculate metrics for a CAP (Confidence-Adaptive Pruning) simulation.

    Args:
        log_path: Path to the CAP simulation log file (JSON).

    Returns:
        Dictionary containing AUCC, final_accuracy, average_prompt_length.
    """
    log_path = Path(log_path)
    if not log_path.exists():
        raise FileNotFoundError(f"CAP log file not found: {log_path}")

    with open(log_path, 'r') as f:
        log_data = json.load(f)

    metrics = calculate_metrics_from_log(log_data, metric_type="cap")
    info(f"CAP metrics calculated: {metrics}")
    return metrics