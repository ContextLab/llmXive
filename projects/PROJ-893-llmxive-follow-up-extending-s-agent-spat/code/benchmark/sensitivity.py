import os
import sys
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config

def load_benchmark_results(filepath: str) -> List[Dict[str, Any]]:
    """Load benchmark results from CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Benchmark results file not found: {filepath}")
    
    results = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results

def calculate_vlm_baseline_accuracy(results: List[Dict[str, Any]]) -> float:
    """Calculate VLM baseline accuracy (exact match rate)."""
    if not results:
        return 0.0
    
    correct = 0
    for row in results:
        if row.get('vlm_pred') and row.get('ground_truth'):
            try:
                if int(row['vlm_pred']) == int(row['ground_truth']):
                    correct += 1
            except (ValueError, TypeError):
                continue
    
    return correct / len(results)

def calculate_symbolic_accuracy_at_threshold(
    results: List[Dict[str, Any]], 
    threshold: float
) -> float:
    """
    Calculate symbolic accuracy assuming a threshold-based decision.
    For this analysis, we simulate how a threshold would affect the
    symbolic solver's performance by treating it as a confidence-based
    classifier.
    
    In this context, we assume the 'f1' score represents the confidence
    or reliability of the prediction. If f1 >= threshold, we count it as
    a 'pass' (correct prediction), otherwise 'fail'.
    
    Note: This is a sensitivity analysis to understand how the acceptance
    threshold (SC-005: 85% of VLM baseline) impacts the verdict.
    """
    if not results:
        return 0.0
    
    # We count a prediction as "accepted" if its F1 score meets the threshold
    # This simulates a scenario where we only trust predictions above a certain confidence
    accepted_count = 0
    total_count = 0
    
    for row in results:
        try:
            f1_score = float(row.get('f1', 0))
            total_count += 1
            if f1_score >= threshold:
                # Check if it was actually correct
                if row.get('exact_match') == 'True' or row.get('exact_match') == 'true' or row.get('exact_match') == '1':
                    accepted_count += 1
        except (ValueError, TypeError):
            continue
    
    if total_count == 0:
        return 0.0
    
    return accepted_count / total_count

def run_sensitivity_analysis(
    results: List[Dict[str, Any]],
    threshold_start: float = 0.0,
    threshold_end: float = 1.0,
    step: float = 0.05
) -> List[Dict[str, Any]]:
    """
    Run sensitivity analysis across a range of thresholds.
    
    Args:
        results: List of benchmark result dictionaries
        threshold_start: Start threshold (inclusive)
        threshold_end: End threshold (inclusive)
        step: Step size for threshold increment
    
    Returns:
        List of dictionaries with threshold and verdict
    """
    analysis_results = []
    
    current_threshold = threshold_start
    while current_threshold <= threshold_end + 1e-9:  # Small epsilon for float comparison
        # Calculate symbolic accuracy at this threshold
        accuracy = calculate_symbolic_accuracy_at_threshold(results, current_threshold)
        
        # Determine verdict based on acceptance criteria (SC-005: >= 85% of VLM baseline)
        # However, for sensitivity analysis, we compare against the threshold itself
        # to see at what threshold the system "passes" or "fails" relative to that threshold
        # 
        # For this specific task, the "verdict" indicates whether the symbolic solver
        # would meet a hypothetical acceptance criterion at that threshold.
        # We interpret "verdict" as: does the accuracy at this threshold meet the threshold?
        # (i.e., is the system self-consistent?)
        #
        # More practically for the research question: 
        # "At what threshold does the symbolic solver's performance become acceptable?"
        # We'll mark "Pass" if accuracy >= threshold (self-consistency)
        # and "Fail" otherwise.
        
        verdict = "Pass" if accuracy >= current_threshold else "Fail"
        
        analysis_results.append({
            'threshold': round(current_threshold, 2),
            'symbolic_accuracy': round(accuracy, 4),
            'verdict': verdict
        })
        
        current_threshold += step
    
    return analysis_results

def save_sensitivity_analysis(
    analysis_results: List[Dict[str, Any]],
    output_path: str
) -> None:
    """Save sensitivity analysis results to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['threshold', 'symbolic_accuracy', 'verdict']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in analysis_results:
            writer.writerow(row)

def main():
    """Main entry point for sensitivity analysis."""
    parser = argparse.ArgumentParser(
        description='Run sensitivity analysis on benchmark results.'
    )
    parser.add_argument(
        '--input',
        type=str,
        default='data/results/benchmark_results.csv',
        help='Path to benchmark results CSV'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/results/sensitivity_analysis.csv',
        help='Path to output sensitivity analysis CSV'
    )
    parser.add_argument(
        '--start',
        type=float,
        default=0.0,
        help='Start threshold for sensitivity sweep'
    )
    parser.add_argument(
        '--end',
        type=float,
        default=1.0,
        help='End threshold for sensitivity sweep'
    )
    parser.add_argument(
        '--step',
        type=float,
        default=0.05,
        help='Step size for threshold increment'
    )
    
    args = parser.parse_args()
    
    print(f"Loading benchmark results from {args.input}...")
    try:
        results = load_benchmark_results(args.input)
        print(f"Loaded {len(results)} benchmark results.")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    
    if not results:
        print("ERROR: No benchmark results found.")
        sys.exit(1)
    
    print(f"Running sensitivity analysis from {args.start} to {args.end} (step={args.step})...")
    analysis_results = run_sensitivity_analysis(
        results,
        threshold_start=args.start,
        threshold_end=args.end,
        step=args.step
    )
    
    print(f"Saving results to {args.output}...")
    save_sensitivity_analysis(analysis_results, args.output)
    
    print(f"Sensitivity analysis complete. {len(analysis_results)} thresholds evaluated.")
    print(f"Output written to: {args.output}")

if __name__ == '__main__':
    main()