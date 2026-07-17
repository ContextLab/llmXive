"""
Threshold Optimization Module for Entropy-Guided Validity Prediction.

This module implements the logic to find the optimal entropy threshold
that minimizes the weighted sum of False Positives and False Negatives.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

from src.utils.validators import load_and_validate_jsonl, EntropyProfile
from src.analysis.logistic_model import load_entropy_profiles_for_analysis

# Configure logging
logger = logging.getLogger(__name__)


def calculate_metrics_at_threshold(
    y_true: np.ndarray,
    entropy_values: np.ndarray,
    threshold: float,
    higher_entropy_is_valid: bool = True
) -> Dict[str, float]:
    """
    Calculate confusion matrix metrics at a specific entropy threshold.

    Args:
        y_true: Array of binary validity labels (1=valid, 0=invalid).
        entropy_values: Array of entropy values for the tokens.
        threshold: The entropy threshold to evaluate.
        higher_entropy_is_valid: If True, entropy > threshold implies valid.
                                 If False, entropy < threshold implies valid.
                                 (Default: True, as higher entropy often correlates
                                 with uncertainty/invalidity in some contexts,
                                 but here we assume we are predicting VALIDITY.
                                 Usually, low entropy = high confidence = likely valid.
                                 However, the task asks to minimize weighted error.
                                 We will treat the direction as a parameter.)

    Returns:
        Dict with 'tp', 'fp', 'tn', 'fn', 'precision', 'recall', 'f1'.
    """
    if higher_entropy_is_valid:
        y_pred = (entropy_values >= threshold).astype(int)
    else:
        y_pred = (entropy_values < threshold).astype(int)

    tp = np.sum((y_true == 1) & (y_pred == 1))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    tn = np.sum((y_true == 0) & (y_pred == 0))
    fn = np.sum((y_true == 1) & (y_pred == 0))

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "tp": int(tp),
        "fp": int(fp),
        "tn": int(tn),
        "fn": int(fn),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1)
    }


def find_optimal_threshold(
    y_true: np.ndarray,
    entropy_values: np.ndarray,
    cost_fp: float = 1.0,
    cost_fn: float = 1.0,
    higher_entropy_is_valid: bool = False,
    num_candidates: int = 100
) -> Tuple[float, Dict[str, Any]]:
    """
    Find the optimal entropy threshold minimizing the weighted cost of errors.

    The cost function is: Cost = (FP * cost_fp) + (FN * cost_fn).

    Args:
        y_true: Array of binary validity labels.
        entropy_values: Array of entropy values.
        cost_fp: Weight for False Positives.
        cost_fn: Weight for False Negatives.
        higher_entropy_is_valid: Direction of the threshold logic.
        num_candidates: Number of threshold candidates to search.

    Returns:
        Tuple of (optimal_threshold, best_metrics_dict).
    """
    if len(y_true) == 0 or len(entropy_values) == 0:
        raise ValueError("Input arrays cannot be empty.")
    if len(y_true) != len(entropy_values):
        raise ValueError("y_true and entropy_values must have the same length.")

    # Sort unique entropy values to use as candidate thresholds
    # We also include the min and max to cover the full range
    unique_values = np.sort(np.unique(entropy_values))
    
    if len(unique_values) < 2:
        # If all values are the same, any threshold outside the range works,
        # but we return the value itself as the threshold.
        threshold = unique_values[0]
        metrics = calculate_metrics_at_threshold(y_true, entropy_values, threshold, higher_entropy_is_valid)
        return threshold, metrics

    # Create candidates: midpoints between unique values + min and max
    candidates = []
    candidates.append(unique_values[0] - 1e-9) # Below min
    for i in range(len(unique_values) - 1):
        mid = (unique_values[i] + unique_values[i+1]) / 2.0
        candidates.append(mid)
    candidates.append(unique_values[-1] + 1e-9) # Above max

    best_threshold = candidates[0]
    min_cost = float('inf')
    best_metrics = {}

    for threshold in candidates:
        metrics = calculate_metrics_at_threshold(y_true, entropy_values, threshold, higher_entropy_is_valid)
        
        # Calculate weighted cost
        cost = (metrics['fp'] * cost_fp) + (metrics['fn'] * cost_fn)
        
        if cost < min_cost:
            min_cost = cost
            best_threshold = threshold
            best_metrics = metrics

    best_metrics['optimal_threshold'] = float(best_threshold)
    best_metrics['weighted_cost'] = float(min_cost)
    best_metrics['cost_fp'] = cost_fp
    best_metrics['cost_fn'] = cost_fn

    return best_threshold, best_metrics


def analyze_thresholds(
    data_path: str,
    output_path: str,
    entropy_field: str = "entropy_mean",
    validity_field: str = "validity",
    cost_fp: float = 1.0,
    cost_fn: float = 1.0,
    higher_entropy_is_valid: bool = False
) -> Dict[str, Any]:
    """
    Main analysis function to load data, find optimal threshold, and write results.

    Args:
        data_path: Path to the input JSONL file containing entropy profiles and labels.
        output_path: Path to write the JSON results.
        entropy_field: Name of the field containing entropy values.
        validity_field: Name of the field containing validity labels.
        cost_fp: Cost weight for False Positives.
        cost_fn: Cost weight for False Negatives.
        higher_entropy_is_valid: Logic direction for thresholding.

    Returns:
        Dictionary containing the analysis results.
    """
    logger.info(f"Loading data from {data_path}")
    
    # Load and validate data
    # The data is expected to be a list of records, each with 'entropy' (list) and 'validity'
    # or flattened entropy values. Based on T022/T023, we expect merged EntropyProfile records.
    # We assume the data has been flattened or we aggregate per-sequence.
    # For threshold optimization, we typically look at token-level entropy vs token-level validity.
    
    records = load_and_validate_jsonl(data_path)
    
    if not records:
        raise ValueError(f"No records found in {data_path}")

    # Extract entropy and validity. 
    # If the data is per-sequence with a list of entropies, we flatten it.
    # Assuming the merged data has a structure like:
    # { "sequence_id": ..., "validity": 0/1, "entropy_profile": { "layers": [ ... ] } }
    # Or if T022 flattened it: { "token_entropy": [ ... ], "token_validity": [ ... ] }
    
    # Let's assume a standard structure where we have a list of entropy values and a corresponding validity.
    # If the input is per-sequence, we might need to aggregate. 
    # For this implementation, we assume the input data has been pre-processed to have 
    # a list of (entropy, validity) pairs or we flatten the sequence-level data.
    
    all_entropies = []
    all_validities = []

    for record in records:
        # Try to find entropy values
        if "entropy_values" in record:
            ent_vals = record["entropy_values"]
        elif "entropy" in record:
            # Could be a single value or a list
            val = record["entropy"]
            if isinstance(val, list):
                ent_vals = val
            else:
                ent_vals = [val]
        else:
            # Fallback to checking nested structures if standard keys missing
            # Assuming T022 output structure
            if "entropy_profile" in record and "layer_entropies" in record["entropy_profile"]:
                ent_vals = record["entropy_profile"]["layer_entropies"]
            else:
                logger.warning(f"Record missing entropy field: {record.get('sequence_id', 'unknown')}")
                continue

        # Get validity (assuming sequence-level validity applies to all tokens, or token-level)
        # If token-level validity exists:
        if "token_validity" in record:
            valid_vals = record["token_validity"]
        else:
            # Assume sequence validity applies to all tokens in the sequence
            seq_validity = record.get("validity", 0)
            valid_vals = [seq_validity] * len(ent_vals)

        if len(ent_vals) != len(valid_vals):
            logger.warning(f"Mismatch in entropy/validity length for {record.get('sequence_id', 'unknown')}. Skipping.")
            continue

        all_entropies.extend(ent_vals)
        all_validities.extend(valid_vals)

    if not all_entropies:
        raise ValueError("No valid entropy/validity pairs found in the dataset.")

    y_true = np.array(all_validities)
    entropy_vals = np.array(all_entropies)

    logger.info(f"Analyzing {len(y_true)} tokens for threshold optimization.")

    optimal_threshold, metrics = find_optimal_threshold(
        y_true, entropy_vals, 
        cost_fp=cost_fp, cost_fn=cost_fn,
        higher_entropy_is_valid=higher_entropy_is_valid
    )

    result = {
        "optimal_threshold": float(optimal_threshold),
        "metrics_at_optimal": metrics,
        "dataset_size": len(y_true),
        "valid_count": int(np.sum(y_true)),
        "invalid_count": int(len(y_true) - np.sum(y_true)),
        "parameters": {
            "cost_fp": cost_fp,
            "cost_fn": cost_fn,
            "higher_entropy_is_valid": higher_entropy_is_valid
        }
    }

    logger.info(f"Optimal threshold found: {optimal_threshold:.4f}")
    logger.info(f"Metrics: {metrics}")

    # Write to disk
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Results written to {output_path}")
    return result


def main():
    """CLI entry point for threshold optimization."""
    import argparse

    parser = argparse.ArgumentParser(description="Find optimal entropy threshold for validity prediction.")
    parser.add_argument("--input", type=str, required=True, help="Path to input JSONL file with entropy profiles and labels.")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON results file.")
    parser.add_argument("--cost-fp", type=float, default=1.0, help="Cost weight for False Positives.")
    parser.add_argument("--cost-fn", type=float, default=1.0, help="Cost weight for False Negatives.")
    parser.add_argument("--higher-entropy-valid", action="store_true", help="If set, higher entropy implies validity.")
    
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        analyze_thresholds(
            data_path=args.input,
            output_path=args.output,
            cost_fp=args.cost_fp,
            cost_fn=args.cost_fn,
            higher_entropy_is_valid=args.higher_entropy_valid
        )
        print(f"Threshold optimization complete. Results saved to {args.output}")
    except Exception as e:
        logger.error(f"Threshold optimization failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
