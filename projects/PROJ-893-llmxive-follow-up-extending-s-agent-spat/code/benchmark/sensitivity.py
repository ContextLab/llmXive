"""
Sensitivity Analysis for Symbolic vs VLM Benchmarking.

Implements the sensitivity analysis sweep algorithm to evaluate how the
symbolic solver's performance changes across different accuracy thresholds.
Generates `data/results/sensitivity_analysis.csv` as the authoritative source
for sensitivity data (Constitution Principle IV).
"""

import os
import sys
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from sibling modules as per API surface
# Note: We assume benchmark_results.csv exists as produced by T019b-final
# If not, we handle it gracefully with an error message.

def load_benchmark_results(file_path: str) -> List[Dict[str, Any]]:
    """
    Load benchmark results from a CSV file.

    Args:
        file_path: Path to the benchmark results CSV file.

    Returns:
        List of dictionaries containing benchmark results.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is malformed or missing required columns.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Benchmark results file not found: {file_path}")

    results = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        required_columns = {'scene_id', 'symbolic_pred', 'vlm_pred', 'ground_truth', 'exact_match', 'f1', 'latency_ms', 'status', 'p_value'}
        
        if not required_columns.issubset(set(reader.fieldnames)):
            missing = required_columns - set(reader.fieldnames)
            raise ValueError(f"Benchmark results file missing required columns: {missing}")

        for row in reader:
            # Convert numeric fields
            try:
                row['exact_match'] = row['exact_match'] == 'True' or row['exact_match'] == 'true' or row['exact_match'] == '1'
                row['f1'] = float(row['f1'])
                row['latency_ms'] = float(row['latency_ms'])
                row['p_value'] = float(row['p_value'])
            except (ValueError, TypeError) as e:
                raise ValueError(f"Malformed data in row {row.get('scene_id', 'unknown')}: {e}")
            results.append(row)

    if not results:
        raise ValueError("Benchmark results file is empty or has no valid data rows.")

    return results

def calculate_vlm_baseline_accuracy(results: List[Dict[str, Any]]) -> float:
    """
    Calculate the baseline accuracy of the VLM predictions.

    Args:
        results: List of benchmark result dictionaries.

    Returns:
        Float representing the VLM baseline accuracy (0.0 to 1.0).
    """
    if not results:
        return 0.0

    correct = sum(1 for r in results if r['vlm_pred'] == r['ground_truth'])
    return correct / len(results)

def calculate_symbolic_accuracy_at_threshold(results: List[Dict[str, Any]], threshold: float) -> float:
    """
    Calculate the symbolic solver's accuracy at a given threshold.
    
    The threshold is applied to the F1 score. A prediction is considered
    'successful' if its F1 score is >= threshold.
    
    Args:
        results: List of benchmark result dictionaries.
        threshold: Accuracy threshold (0.0 to 1.0).

    Returns:
        Float representing the symbolic solver's success rate at the threshold.
    """
    if not results:
        return 0.0

    # Filter results where the symbolic solver's F1 score meets the threshold
    # We consider a prediction successful if F1 >= threshold
    successful = sum(1 for r in results if r['f1'] >= threshold)
    return successful / len(results)

def calculate_false_positive_rate(results: List[Dict[str, Any]], threshold: float) -> float:
    """
    Calculate the false positive rate at a given threshold.
    
    A false positive is defined as a case where the symbolic solver's F1 score
    meets the threshold (>= threshold), but the prediction is incorrect
    (symbolic_pred != ground_truth).
    
    Args:
        results: List of benchmark result dictionaries.
        threshold: Accuracy threshold (0.0 to 1.0).

    Returns:
        Float representing the false positive rate (0.0 to 1.0).
    """
    if not results:
        return 0.0

    # Count cases where F1 >= threshold (predicted positive)
    predicted_positive = sum(1 for r in results if r['f1'] >= threshold)
    
    if predicted_positive == 0:
        return 0.0

    # Count cases where F1 >= threshold AND prediction is wrong (false positive)
    false_positives = sum(1 for r in results if r['f1'] >= threshold and r['symbolic_pred'] != r['ground_truth'])
    
    return false_positives / predicted_positive

def run_sensitivity_analysis(results: List[Dict[str, Any]], start: float = 0.50, end: float = 0.95, step: float = 0.05) -> List[Dict[str, float]]:
    """
    Run the sensitivity analysis sweep algorithm.

    Sweeps the accuracy threshold from `start` to `end` (inclusive) with `step` size.
    Calculates success_rate and false_positive_rate for each threshold.

    Args:
        results: List of benchmark result dictionaries.
        start: Starting threshold value (default 0.50).
        end: Ending threshold value (default 0.95).
        step: Step size for the sweep (default 0.05).

    Returns:
        List of dictionaries containing threshold, success_rate, and false_positive_rate.
    """
    analysis_results = []
    current_threshold = start
    
    # Use a small epsilon for float comparison to ensure 'end' is included
    epsilon = 1e-9
    
    while current_threshold <= end + epsilon:
        # Clamp to end to avoid floating point drift
        threshold = min(current_threshold, end)
        
        success_rate = calculate_symbolic_accuracy_at_threshold(results, threshold)
        fpr = calculate_false_positive_rate(results, threshold)
        
        analysis_results.append({
            'threshold': round(threshold, 2),
            'success_rate': round(success_rate, 4),
            'false_positive_rate': round(fpr, 4)
        })
        
        current_threshold += step

    return analysis_results

def save_sensitivity_analysis(analysis_results: List[Dict[str, float]], output_path: str) -> None:
    """
    Save sensitivity analysis results to a CSV file.

    Args:
        analysis_results: List of dictionaries with analysis data.
        output_path: Path to the output CSV file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['threshold', 'success_rate', 'false_positive_rate']
    
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(analysis_results)

def main():
    """
    Main entry point for the sensitivity analysis script.
    """
    parser = argparse.ArgumentParser(
        description='Run sensitivity analysis on benchmark results.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--input',
        type=str,
        default='data/results/benchmark_results.csv',
        help='Path to the benchmark results CSV file.'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='data/results/sensitivity_analysis.csv',
        help='Path to the output sensitivity analysis CSV file.'
    )
    
    parser.add_argument(
        '--start',
        type=float,
        default=0.50,
        help='Starting threshold value for the sweep.'
    )
    
    parser.add_argument(
        '--end',
        type=float,
        default=0.95,
        help='Ending threshold value for the sweep.'
    )
    
    parser.add_argument(
        '--step',
        type=float,
        default=0.05,
        help='Step size for the threshold sweep.'
    )
    
    args = parser.parse_args()
    
    print(f"Loading benchmark results from: {args.input}")
    try:
        results = load_benchmark_results(args.input)
        print(f"Loaded {len(results)} benchmark results.")
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: Failed to load benchmark results: {e}")
        sys.exit(1)
    
    print(f"Running sensitivity analysis from {args.start} to {args.end} with step {args.step}...")
    analysis_results = run_sensitivity_analysis(results, args.start, args.end, args.step)
    
    print(f"Saving sensitivity analysis to: {args.output}")
    try:
        save_sensitivity_analysis(analysis_results, args.output)
        print("Sensitivity analysis completed successfully.")
    except IOError as e:
        print(f"ERROR: Failed to save sensitivity analysis: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()