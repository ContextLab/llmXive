import argparse
import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import math
import statistics

# Import from utils.metrics as per API surface
from utils.metrics import compute_cohen_d, t_test_independent, ancova

def load_evaluation_results(file_path: str) -> List[Dict[str, Any]]:
    """Load evaluation results from a JSONL file."""
    results = []
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Evaluation results file not found: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                results.append(json.loads(line))
    return results

def load_stratified_data(file_path: str) -> List[Dict[str, Any]]:
    """Load stratified data from a CSV file."""
    import csv
    data = []
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Stratified data file not found: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def extract_group_data(results: List[Dict[str, Any]], stratified_data: List[Dict[str, Any]]) -> Dict[str, List[float]]:
    """
    Extract metric values (BLEU or F1) grouped by 'group' (High, Medium, Low).
    Merges inference results with stratified data to ensure group assignment is present.
    """
    # Map file_path to group from stratified data
    path_to_group = {}
    for row in stratified_data:
        # Handle potential missing columns gracefully
        if 'file_path' in row and 'group' in row:
            path_to_group[row['file_path']] = row['group']
    
    groups: Dict[str, List[float]] = {'High': [], 'Medium': [], 'Low': []}
    
    for res in results:
        file_path = res.get('file_path')
        if not file_path or file_path not in path_to_group:
            continue
        
        group = path_to_group[file_path]
        
        # Determine which metric to use: BLEU for summary, F1 for bug localization
        # For group separation verification, we typically look at the primary accuracy metric.
        # Let's use BLEU if available, otherwise F1.
        if 'bleu_score' in res and res['bleu_score'] is not None:
            val = float(res['bleu_score'])
        elif 'f1_score' in res and res['f1_score'] is not None:
            val = float(res['f1_score'])
        else:
            continue
        
        if group in groups:
            groups[group].append(val)
        
    return groups

def compute_power_effect_size(n1: int, n2: int, mean1: float, mean2: float, std1: float, std2: float, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Compute Cohen's d and estimate statistical power.
    Uses a simplified approximation for power based on effect size and sample size.
    """
    if std1 == 0 and std2 == 0:
        return {"cohens_d": 0.0, "power_estimate": 0.0, "error": "Zero variance"}
    
    # Pooled standard deviation
    n1_f = float(n1)
    n2_f = float(n2)
    pooled_std = math.sqrt(((n1_f - 1) * (std1 ** 2) + (n2_f - 1) * (std2 ** 2)) / (n1_f + n2_f - 2))
    
    if pooled_std == 0:
        return {"cohens_d": 0.0, "power_estimate": 0.0, "error": "Pooled std is zero"}
    
    d = (mean1 - mean2) / pooled_std
    
    # Approximate power calculation using normal distribution approximation
    # Effect size d, sample sizes n1, n2
    # Non-centrality parameter lambda
    lambda_ncp = d * math.sqrt((n1_f * n2_f) / (n1_f + n2_f))
    
    # Critical z for two-tailed test at alpha
    # Using a rough approximation for Z critical (1.96 for 0.05)
    z_crit = 1.96 
    
    # Power is probability that Z > z_crit - lambda or Z < -z_crit - lambda
    # Approximation: Power ~ Phi(lambda - z_crit) + Phi(-lambda - z_crit)
    # Since we care about detecting a difference, we look at the tail.
    # Simple heuristic for power: if |lambda| is large, power is high.
    # Using a standard normal CDF approximation
    def norm_cdf(x):
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))
    
    power = norm_cdf(lambda_ncp - z_crit) + norm_cdf(-lambda_ncp - z_crit)
    # Ensure power is bounded [0, 1]
    power = max(0.0, min(1.0, power))
    
    return {
        "cohens_d": d,
        "power_estimate": power,
        "n1": n1,
        "n2": n2,
        "mean1": mean1,
        "mean2": mean2,
        "std1": std1,
        "std2": std2
    }

def verify_group_separation(groups: Dict[str, List[float]], threshold: float = 0.5) -> Dict[str, Any]:
    """
    Verify if the effect size (Cohen's d) between High and Low groups exceeds the threshold.
    Also estimates statistical power for this comparison.
    """
    high_data = groups.get('High', [])
    low_data = groups.get('Low', [])
    
    if not high_data or not low_data:
        return {
            "passed": False,
            "reason": "Insufficient data in High or Low groups",
            "cohens_d": None,
            "power_estimate": None
        }
    
    mean_high = statistics.mean(high_data)
    mean_low = statistics.mean(low_data)
    std_high = statistics.stdev(high_data) if len(high_data) > 1 else 0.0
    std_low = statistics.stdev(low_data) if len(low_data) > 1 else 0.0
    
    result = compute_power_effect_size(len(high_data), len(low_data), mean_high, mean_low, std_high, std_low)
    
    cohens_d = result["cohens_d"]
    power = result["power_estimate"]
    
    # Check if effect size magnitude is > threshold
    passed = abs(cohens_d) > threshold
    
    return {
        "passed": passed,
        "reason": "Effect size threshold met" if passed else f"Effect size {cohens_d:.4f} below threshold {threshold}",
        "cohens_d": cohens_d,
        "power_estimate": power,
        "high_stats": {"mean": mean_high, "std": std_high, "n": len(high_data)},
        "low_stats": {"mean": mean_low, "std": std_low, "n": len(low_data)}
    }

def run_group_separation_and_power(evaluation_file: str, stratified_file: str, threshold: float = 0.5) -> Dict[str, Any]:
    """
    Main logic for T030: Verify group separation (effect size > 0.5) and estimate power.
    """
    try:
        results = load_evaluation_results(evaluation_file)
        stratified = load_stratified_data(stratified_file)
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
    
    groups = extract_group_data(results, stratified)
    
    verification = verify_group_separation(groups, threshold)
    
    return {
        "status": "success",
        "verification": verification,
        "groups_summary": {k: {"count": len(v)} for k, v in groups.items()}
    }

def main():
    parser = argparse.ArgumentParser(description="T030: Group separation verification and power estimation")
    parser.add_argument("--eval-file", required=True, help="Path to evaluation results JSONL")
    parser.add_argument("--stratified-file", required=True, help="Path to stratified data CSV")
    parser.add_argument("--threshold", type=float, default=0.5, help="Effect size threshold (default 0.5)")
    parser.add_argument("--output", required=True, help="Path to output JSON report")
    
    args = parser.parse_args()
    
    report = run_group_separation_and_power(args.eval_file, args.stratified_file, args.threshold)
    
    # Ensure output directory exists
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"Report written to {args.output}")
    if report.get("verification", {}).get("passed"):
        print("SUCCESS: Group separation effect size exceeds threshold.")
    else:
        print(f"WARNING: Group separation effect size does not exceed threshold. {report.get('verification', {}).get('reason')}")

if __name__ == "__main__":
    main()
