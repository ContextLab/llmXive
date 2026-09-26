import os
import sys
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent to path for imports if running as script
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import Config

def load_benchmark_results(filepath: str) -> List[Dict[str, Any]]:
    """Load benchmark results from CSV."""
    results = []
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Benchmark results file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results

def calculate_vlm_baseline_accuracy(results: List[Dict[str, Any]]) -> float:
    """Calculate the VLM baseline accuracy from the benchmark results."""
    if not results:
        return 0.0
    
    correct = 0
    total = 0
    for row in results:
        if 'vlm_pred' in row and 'ground_truth' in row:
            try:
                vlm_pred = int(row['vlm_pred'])
                ground_truth = int(row['ground_truth'])
                total += 1
                if vlm_pred == ground_truth:
                    correct += 1
            except (ValueError, TypeError):
                continue
    
    if total == 0:
        return 0.0
    return correct / total

def calculate_symbolic_accuracy_at_threshold(
    results: List[Dict[str, Any]], 
    threshold: float
) -> float:
    """
    Calculate symbolic accuracy assuming the symbolic solver only succeeds
    if its accuracy metric (or confidence proxy) meets the threshold.
    
    Since the benchmark_results.csv contains 'f1' and 'exact_match' but not
    a raw 'confidence' score, we interpret the task as:
    "What is the accuracy of the symbolic solver if we filter out predictions
    where the symbolic performance metric (e.g., F1 or Exact Match) is below
    a certain threshold?"
    
    However, the CSV contains per-scene metrics. A more standard sensitivity
    analysis for a binary classifier involves sweeping a decision threshold.
    Here, we treat 'exact_match' (1.0 or 0.0) as the binary outcome.
    
    If we assume the 'threshold' applies to a latent confidence score that
    correlates with the 'f1' score (which is 0.0 or 1.0 for exact match tasks
    usually), the analysis is trivial unless we have a continuous score.
    
    Given the data structure, we will interpret the 'threshold' as a filter
    on the 'f1' score (or a proxy confidence derived from it). If F1 < threshold,
    we treat the prediction as 'abstained' (not counted in accuracy).
    
    Wait, the task description says: "sweeping the accuracy threshold... across a range".
    This usually implies: "If the VLM baseline accuracy is X, and we require the
    symbolic solver to be Y% of X, what is the verdict?"
    
    Let's re-read the task: "Read VLM baseline accuracy... Sweep threshold... Output: threshold, verdict".
    This suggests the threshold is the *target* ratio relative to the baseline.
    
    Interpretation:
    1. Calculate VLM Baseline Accuracy (A_vlm).
    2. Calculate Symbolic Accuracy (A_sym).
    3. Sweep a threshold T (e.g., 0.50 to 0.95).
    4. Verdict = "Pass" if (A_sym / A_vlm) >= T, else "Fail".
    
    This matches the "Threshold Justification" assumption: "Is the 85% threshold
    reasonable? Let's see how the Pass/Fail verdict changes as we vary the threshold."
    """
    if not results:
        return 0.0
    
    symbolic_correct = 0
    total = 0
    
    for row in results:
        if 'symbolic_pred' in row and 'ground_truth' in row:
            try:
                sym = int(row['symbolic_pred'])
                gt = int(row['ground_truth'])
                total += 1
                if sym == gt:
                    symbolic_correct += 1
            except (ValueError, TypeError):
                continue
    
    if total == 0:
        return 0.0
    return symbolic_correct / total

def run_sensitivity_analysis(
    results: List[Dict[str, Any]],
    start: float = 0.50,
    end: float = 0.95,
    step: float = 0.05
) -> List[Dict[str, Any]]:
    """
    Run sensitivity analysis by sweeping the acceptance threshold.
    
    The threshold represents the required ratio of Symbolic Accuracy to VLM Accuracy.
    Verdict is 'Pass' if (Sym_Acc / VLM_Acc) >= threshold.
    """
    vlm_acc = calculate_vlm_baseline_accuracy(results)
    sym_acc = calculate_symbolic_accuracy_at_threshold(results, 0.0) # Calculate raw symbolic accuracy
    
    # Handle zero division
    if vlm_acc == 0.0:
        # If VLM is 0, we can't compute a ratio. 
        # We'll assume symbolic cannot exceed 0, so all thresholds fail unless threshold is 0.
        # But practically, this is an error case.
        # Let's return a specific verdict for this edge case.
        sensitivity_data = []
        current = start
        while current <= end + 1e-9:
            verdict = "N/A (Baseline Zero)"
            sensitivity_data.append({
                "threshold": round(current, 2),
                "verdict": verdict,
                "vlm_accuracy": vlm_acc,
                "symbolic_accuracy": sym_acc
            })
            current += step
        return sensitivity_data

    ratio = sym_acc / vlm_acc
    
    sensitivity_data = []
    current = start
    while current <= end + 1e-9:
        # Avoid floating point issues
        if current > end:
            current = end
        
        if ratio >= current:
            verdict = "Pass"
        else:
            verdict = "Fail"
        
        sensitivity_data.append({
            "threshold": round(current, 2),
            "verdict": verdict,
            "vlm_accuracy": round(vlm_acc, 4),
            "symbolic_accuracy": round(sym_acc, 4),
            "ratio": round(ratio, 4)
        })
        current += step
    
    return sensitivity_data

def save_sensitivity_analysis(
    data: List[Dict[str, Any]], 
    output_path: str
) -> None:
    """Save sensitivity analysis results to CSV."""
    if not data:
        raise ValueError("No data to save")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

def main():
    """Main entry point for sensitivity analysis."""
    parser = argparse.ArgumentParser(description="Run sensitivity analysis on benchmark results.")
    parser.add_argument(
        "--results",
        type=str,
        default="data/results/benchmark_results.csv",
        help="Path to the benchmark results CSV file."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/results/sensitivity_analysis.csv",
        help="Path to save the sensitivity analysis CSV."
    )
    parser.add_argument(
        "--start",
        type=float,
        default=0.50,
        help="Start threshold value."
    )
    parser.add_argument(
        "--end",
        type=float,
        default=0.95,
        help="End threshold value."
    )
    parser.add_argument(
        "--step",
        type=float,
        default=0.05,
        help="Step size for threshold sweep."
    )
    
    args = parser.parse_args()
    
    print(f"Loading benchmark results from: {args.results}")
    try:
        results = load_benchmark_results(args.results)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    
    if not results:
        print("ERROR: Benchmark results file is empty.")
        sys.exit(1)
    
    print(f"Running sensitivity analysis (start={args.start}, end={args.end}, step={args.step})...")
    analysis_data = run_sensitivity_analysis(results, args.start, args.end, args.step)
    
    print(f"Saving results to: {args.output}")
    save_sensitivity_analysis(analysis_data, args.output)
    
    print("Sensitivity analysis complete.")

if __name__ == "__main__":
    main()