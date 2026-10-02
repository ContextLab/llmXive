import os
import sys
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import Config

def load_benchmark_results(filepath: str) -> List[Dict[str, Any]]:
    """
    Load benchmark results from a CSV file.
    
    Args:
        filepath: Path to the benchmark results CSV.
        
    Returns:
        List of dictionaries representing each row.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Benchmark results file not found: {filepath}")
    
    results = []
    required_columns = {'scene_id', 'symbolic_pred', 'vlm_pred', 'ground_truth', 'exact_match', 'f1', 'latency_ms', 'status'}
    
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Verify required columns exist
        if reader.fieldnames is None:
            raise ValueError("CSV file is empty or has no header.")
        
        missing_cols = required_columns - set(reader.fieldnames)
        if missing_cols:
            raise ValueError(f"Missing required columns in benchmark results: {missing_cols}")
        
        for row in reader:
            # Convert numeric fields
            row['exact_match'] = row['exact_match'].lower() == 'true'
            row['f1'] = float(row['f1'])
            row['latency_ms'] = float(row['latency_ms'])
            results.append(row)
    
    return results

def calculate_vlm_baseline_accuracy(results: List[Dict[str, Any]]) -> float:
    """
    Calculate the overall accuracy of the VLM baseline.
    
    Args:
        results: List of benchmark result dictionaries.
        
    Returns:
        Accuracy as a float between 0 and 1.
    """
    if not results:
        return 0.0
    
    correct = sum(1 for r in results if r['vlm_pred'] == r['ground_truth'])
    return correct / len(results)

def calculate_symbolic_accuracy_at_threshold(
    results: List[Dict[str, Any]], 
    threshold: float
) -> float:
    """
    Calculate symbolic accuracy considering only cases where VLM confidence 
    (proxied by F1 score) exceeds a threshold.
    
    Note: Since we don't have explicit confidence scores, we use the F1 score
    from the benchmark results as a proxy for VLM confidence/quality.
    
    Args:
        results: List of benchmark result dictionaries.
        threshold: Minimum F1 score threshold for inclusion.
        
    Returns:
        Symbolic accuracy for filtered results, or 0.0 if no results match threshold.
    """
    filtered = [r for r in results if r['f1'] >= threshold]
    
    if not filtered:
        return 0.0
    
    correct = sum(1 for r in filtered if r['symbolic_pred'] == r['ground_truth'])
    return correct / len(filtered)

def calculate_false_positive_rate(
    results: List[Dict[str, Any]], 
    threshold: float
) -> float:
    """
    Calculate the false positive rate of the symbolic solver at a given threshold.
    
    A false positive is defined as: VLM is correct (F1 >= threshold) but 
    Symbolic is incorrect.
    
    Args:
        results: List of benchmark result dictionaries.
        threshold: Minimum F1 score threshold for VLM correctness.
        
    Returns:
        False positive rate as a float between 0 and 1.
    """
    filtered = [r for r in results if r['f1'] >= threshold]
    
    if not filtered:
        return 0.0
    
    false_positives = sum(
        1 for r in filtered 
        if r['vlm_pred'] == r['ground_truth'] and r['symbolic_pred'] != r['ground_truth']
    )
    
    return false_positives / len(filtered)

def run_sensitivity_analysis(
    results: List[Dict[str, Any]], 
    min_threshold: float = 0.50, 
    max_threshold: float = 0.95, 
    step: float = 0.05
) -> List[Dict[str, Any]]:
    """
    Run sensitivity analysis by sweeping the accuracy threshold.
    
    Args:
        results: List of benchmark result dictionaries.
        min_threshold: Minimum threshold value.
        max_threshold: Maximum threshold value.
        step: Step size for the sweep.
        
    Returns:
        List of dictionaries containing threshold, success_rate, and false_positive_rate.
    """
    analysis_results = []
    
    current_threshold = min_threshold
    while current_threshold <= max_threshold + 1e-9:  # Floating point tolerance
        success_rate = calculate_symbolic_accuracy_at_threshold(results, current_threshold)
        fpr = calculate_false_positive_rate(results, current_threshold)
        
        analysis_results.append({
            'threshold': round(current_threshold, 2),
            'success_rate': round(success_rate, 4),
            'false_positive_rate': round(fpr, 4)
        })
        
        current_threshold += step
    
    return analysis_results

def save_sensitivity_analysis(
    analysis_results: List[Dict[str, Any]], 
    output_path: str
) -> None:
    """
    Save sensitivity analysis results to a CSV file.
    
    Args:
        analysis_results: List of analysis result dictionaries.
        output_path: Path for the output CSV file.
    """
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['threshold', 'success_rate', 'false_positive_rate']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(analysis_results)

def main():
    """Main entry point for sensitivity analysis."""
    parser = argparse.ArgumentParser(
        description='Perform sensitivity analysis on benchmark results.'
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
        help='Path for the output sensitivity analysis CSV file.'
    )
    parser.add_argument(
        '--min-threshold', 
        type=float, 
        default=0.50,
        help='Minimum threshold for the sweep (default: 0.50).'
    )
    parser.add_argument(
        '--max-threshold', 
        type=float, 
        default=0.95,
        help='Maximum threshold for the sweep (default: 0.95).'
    )
    parser.add_argument(
        '--step', 
        type=float, 
        default=0.05,
        help='Step size for the sweep (default: 0.05).'
    )
    
    args = parser.parse_args()
    
    print(f"Loading benchmark results from {args.input}...")
    try:
        results = load_benchmark_results(args.input)
        print(f"Loaded {len(results)} benchmark results.")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"ERROR: Invalid data format - {e}")
        sys.exit(1)
    
    if len(results) == 0:
        print("ERROR: No benchmark results found to analyze.")
        sys.exit(1)
    
    print(f"Running sensitivity analysis from {args.min_threshold} to {args.max_threshold} with step {args.step}...")
    analysis_results = run_sensitivity_analysis(
        results, 
        args.min_threshold, 
        args.max_threshold, 
        args.step
    )
    
    print(f"Saving sensitivity analysis to {args.output}...")
    save_sensitivity_analysis(analysis_results, args.output)
    
    print(f"Sensitivity analysis complete. {len(analysis_results)} thresholds evaluated.")
    print(f"Output written to: {args.output}")

if __name__ == '__main__':
    main()