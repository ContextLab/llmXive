"""
Sensitivity Analysis Module for Robustness Index Calculation.

This module implements the sensitivity analysis to determine the robustness
of motion labels (High/Low) across varying optical flow magnitude thresholds.
It generates a CSV file with threshold values and the corresponding Robustness Index.
"""

import csv
import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

# Constants
THRESHOLD_MIN = 0.0
THRESHOLD_MAX = 1.0
THRESHOLD_STEP = 0.1


def load_motion_labels(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load motion labels from a JSON file.

    Args:
        file_path: Path to the motion_labels.json file.

    Returns:
        List of dictionaries containing motion label data.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Motion labels file not found: {file_path}")

    with open(file_path, 'r') as f:
        data = json.load(f)

    # Ensure data is a list of samples
    if isinstance(data, dict) and 'samples' in data:
        return data['samples']
    elif isinstance(data, list):
        return data
    else:
        raise ValueError(f"Unexpected data format in {file_path}. Expected list or dict with 'samples' key.")


def calculate_motion_label(magnitude: float, threshold: float) -> str:
    """
    Determine the motion label based on optical flow magnitude and threshold.

    Args:
        magnitude: The optical flow magnitude value.
        threshold: The threshold value for classification.

    Returns:
        'High' if magnitude >= threshold, 'Low' otherwise.
    """
    return "High" if magnitude >= threshold else "Low"


def calculate_robustness_index(samples: List[Dict[str, Any]], thresholds: List[float]) -> Dict[float, float]:
    """
    Calculate the Robustness Index for each threshold.

    The Robustness Index is defined as:
    (Number of samples where motion label remains unchanged across adjacent threshold steps)
    / (Total samples) * 100

    Args:
        samples: List of sample dictionaries containing 'optical_flow_magnitude'.
        thresholds: List of threshold values to evaluate.

    Returns:
        Dictionary mapping each threshold to its Robustness Index (percentage).
    """
    if not samples:
        return {t: 0.0 for t in thresholds}

    robustness_metrics = {}

    for i, threshold in enumerate(thresholds):
        # Get labels for current threshold
        current_labels = [calculate_motion_label(s['optical_flow_magnitude'], threshold) for s in samples]

        # For the first threshold, we assume stability as there's no previous step
        # However, the definition implies "across adjacent threshold steps".
        # To be precise, we calculate stability relative to the NEXT threshold if it exists,
        # or the PREVIOUS if it's the last.
        # Standard interpretation for a sweep: Compare label at T_i with label at T_{i+1} (or T_{i-1}).
        # Let's compare T_i with T_{i+1} for i < len-1, and T_i with T_{i-1} for i == len-1.
        # Actually, the most robust way is to compare T_i with T_{i+1} for all i where i+1 exists.
        # If a sample's label doesn't change between T_i and T_{i+1}, it's stable at T_i.
        # What about the last threshold? It has no next. We can compare with previous.
        # Let's define: Stable at T_i if label(T_i) == label(T_{i+1}) for i < N-1,
        # and label(T_i) == label(T_{i-1}) for i == N-1.

        stable_count = 0
        total_samples = len(samples)

        if i < len(thresholds) - 1:
            # Compare with next threshold
            next_threshold = thresholds[i + 1]
            next_labels = [calculate_motion_label(s['optical_flow_magnitude'], next_threshold) for s in samples]
            for curr, nxt in zip(current_labels, next_labels):
                if curr == nxt:
                    stable_count += 1
        else:
            # Last threshold: compare with previous
            prev_threshold = thresholds[i - 1]
            prev_labels = [calculate_motion_label(s['optical_flow_magnitude'], prev_threshold) for s in samples]
            for curr, prv in zip(current_labels, prev_labels):
                if curr == prv:
                    stable_count += 1

        index_value = (stable_count / total_samples) * 100.0
        robustness_metrics[threshold] = index_value

    return robustness_metrics


def run_sensitivity_analysis(
    motion_labels_path: Path,
    output_path: Path,
    threshold_min: float = THRESHOLD_MIN,
    threshold_max: float = THRESHOLD_MAX,
    threshold_step: float = THRESHOLD_STEP
) -> Path:
    """
    Run the full sensitivity analysis pipeline.

    1. Load motion labels from JSON.
    2. Generate threshold values.
    3. Calculate Robustness Index for each threshold.
    4. Write results to CSV.

    Args:
        motion_labels_path: Path to the input motion_labels.json.
        output_path: Path where the output CSV will be written.
        threshold_min: Minimum threshold value.
        threshold_max: Maximum threshold value.
        threshold_step: Step size for threshold iteration.

    Returns:
        Path to the generated CSV file.

    Raises:
        FileNotFoundError: If input file is missing.
        ValueError: If input data is invalid.
    """
    # 1. Load data
    samples = load_motion_labels(motion_labels_path)
    if not samples:
        raise ValueError("No samples found in motion labels file.")

    # Validate required field
    if 'optical_flow_magnitude' not in samples[0]:
        raise ValueError("Sample data missing 'optical_flow_magnitude' field.")

    # 2. Generate thresholds
    # Use numpy to handle floating point range accurately
    thresholds = np.arange(threshold_min, threshold_max + threshold_step, threshold_step).tolist()
    # Ensure we don't exceed max due to floating point errors
    thresholds = [t if t <= threshold_max + 1e-9 else threshold_max for t in thresholds]
    # Deduplicate and sort
    thresholds = sorted(list(set(thresholds)))

    # 3. Calculate Robustness Index
    metrics = calculate_robustness_index(samples, thresholds)

    # 4. Write CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['threshold', 'robustness_metric'])
        for t in thresholds:
            # Round to avoid floating point representation issues in CSV
            writer.writerow([round(t, 2), round(metrics[t], 2)])

    return output_path


def main():
    """Main entry point for the sensitivity analysis script."""
    parser = argparse.ArgumentParser(
        description="Run sensitivity analysis to calculate Robustness Index."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/motion_labels.json"),
        help="Path to the input motion_labels.json file."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/sensitivity_analysis.csv"),
        help="Path to the output CSV file."
    )
    parser.add_argument(
        "--min-threshold",
        type=float,
        default=THRESHOLD_MIN,
        help=f"Minimum threshold value (default: {THRESHOLD_MIN})"
    )
    parser.add_argument(
        "--max-threshold",
        type=float,
        default=THRESHOLD_MAX,
        help=f"Maximum threshold value (default: {THRESHOLD_MAX})"
    )
    parser.add_argument(
        "--step",
        type=float,
        default=THRESHOLD_STEP,
        help=f"Threshold step size (default: {THRESHOLD_STEP})"
    )

    args = parser.parse_args()

    try:
        output_file = run_sensitivity_analysis(
            motion_labels_path=args.input,
            output_path=args.output,
            threshold_min=args.min_threshold,
            threshold_max=args.max_threshold,
            threshold_step=args.step
        )
        print(f"Sensitivity analysis complete. Results written to: {output_file}")
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
