import math
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from scipy import stats
from scipy.stats import ttest_rel, shapiro, wilcoxon
import json
import csv
from pathlib import Path
from config import get_path, ensure_directories

def load_exploration_logs() -> List[Dict[str, Any]]:
    """Load exploration logs from data/results/exploration_logs.jsonl."""
    log_path = get_path("results", "exploration_logs.jsonl")
    if not log_path.exists():
        raise FileNotFoundError(f"Exploration logs not found at {log_path}")
    
    logs = []
    with open(log_path, 'r') as f:
        for line in f:
            if line.strip():
                logs.append(json.loads(line))
    return logs

def load_scores_map() -> Dict[str, float]:
    """Load regularity scores from data/processed/regularity_scores.csv into a map."""
    scores_path = get_path("processed", "regularity_scores.csv")
    if not scores_path.exists():
        raise FileNotFoundError(f"Regularity scores not found at {scores_path}")
    
    scores_map = {}
    with open(scores_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            repo_id = row['repo_id']
            score = float(row['regularity_score'])
            scores_map[repo_id] = score
    return scores_map

def calculate_regression_analysis(
    scores_map: Dict[str, float], 
    logs: List[Dict[str, Any]], 
    metric_key: str = "context_precision"
) -> Tuple[float, float]:
    """
    Perform regression analysis correlating regularity_score with performance delta.
    Returns (slope, r_squared).
    """
    # Build list of (score, metric_value) pairs
    pairs = []
    for log in logs:
        repo_id = log.get('repo_id')
        if repo_id and repo_id in scores_map:
            metric_val = log.get(metric_key)
            if metric_val is not None:
                pairs.append((scores_map[repo_id], float(metric_val)))
    
    if len(pairs) < 2:
        return 0.0, 0.0
    
    x_vals = [p[0] for p in pairs]
    y_vals = [p[1] for p in pairs]
    
    # Calculate regression
    n = len(pairs)
    sum_x = sum(x_vals)
    sum_y = sum(y_vals)
    sum_xy = sum(x * y for x, y in pairs)
    sum_x2 = sum(x ** 2 for x in x_vals)
    
    denom = n * sum_x2 - sum_x ** 2
    if denom == 0:
        return 0.0, 0.0
    
    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n
    
    # Calculate R-squared
    y_mean = sum_y / n
    ss_tot = sum((y - y_mean) ** 2 for y in y_vals)
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in pairs)
    
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    
    return slope, r_squared

def calc_degradation(baseline_metric: float, lite_metric: float) -> float:
    """Calculate performance degradation percentage: (baseline - lite) / baseline * 100."""
    if baseline_metric == 0:
        return 0.0
    return ((baseline_metric - lite_metric) / baseline_metric) * 100

def run_ttest(
    baseline_vals: List[float], 
    lite_vals: List[float]
) -> Tuple[float, str]:
    """
    Run statistical test (t-test or Wilcoxon) based on normality check.
    Returns (p_value, test_name).
    """
    if len(baseline_vals) != len(lite_vals) or len(baseline_vals) < 2:
        return 1.0, "insufficient_data"
    
    # Normality check
    stat, p_normal = shapiro(baseline_vals)
    use_ttest = p_normal > 0.05
    
    # Also check lite_vals normality
    stat_lite, p_normal_lite = shapiro(lite_vals)
    use_ttest = use_ttest and (p_normal_lite > 0.05)
    
    if use_ttest:
        stat, p_val = ttest_rel(baseline_vals, lite_vals)
        return float(p_val), "t-test"
    else:
        stat, p_val = wilcoxon(baseline_vals, lite_vals)
        return float(p_val), "wilcoxon"

def calculate_effect_size(
    baseline_vals: List[float], 
    lite_vals: List[float]
) -> float:
    """Calculate Cohen's d effect size."""
    if len(baseline_vals) < 2 or len(lite_vals) < 2:
        return 0.0
    
    mean1 = np.mean(baseline_vals)
    mean2 = np.mean(lite_vals)
    std1 = np.std(baseline_vals, ddof=1)
    std2 = np.std(lite_vals, ddof=1)
    
    pooled_std = math.sqrt((std1**2 + std2**2) / 2)
    if pooled_std == 0:
        return 0.0
    
    return (mean1 - mean2) / pooled_std

def find_threshold(scores: List[float], metrics: List[float]) -> float:
    """
    Find the boundary threshold where performance significantly degrades.
    Uses a simple heuristic: find the score where metric drops below mean - std.
    """
    if len(scores) != len(metrics) or len(scores) < 2:
        return 0.0
    
    mean_metric = np.mean(metrics)
    std_metric = np.std(metrics)
    threshold_val = mean_metric - std_metric
    
    # Sort by score and find transition point
    paired = sorted(zip(scores, metrics))
    
    for i in range(len(paired) - 1):
        if paired[i][1] >= threshold_val and paired[i+1][1] < threshold_val:
            return (paired[i][0] + paired[i+1][0]) / 2
    
    return paired[0][0] if paired else 0.0

def calculate_performance_degradation_irregular(
    scores_map: Dict[str, float], 
    logs: List[Dict[str, Any]], 
    threshold: float = 0.5,
    metric_key: str = "context_precision"
) -> float:
    """
    Calculate average degradation for the 'Irregular' set (scores < threshold).
    Compares Lite metrics against Baseline metrics.
    """
    irregular_degradations = []
    
    for log in logs:
        repo_id = log.get('repo_id')
        if not repo_id or repo_id not in scores_map:
            continue
        
        score = scores_map[repo_id]
        if score >= threshold:
            continue
        
        # Extract baseline and lite metrics from log
        # Assuming log has 'baseline_metric' and 'lite_metric' or similar structure
        # Based on T023 structure, logs might contain separate entries or combined
        baseline_val = log.get('baseline_context_precision')
        lite_val = log.get('context_precision')
        
        if baseline_val is not None and lite_val is not None:
            degradation = calc_degradation(baseline_val, lite_val)
            irregular_degradations.append(degradation)
    
    if not irregular_degradations:
        return 0.0
    
    return np.mean(irregular_degradations)

def generate_statistical_summary() -> Dict[str, Any]:
    """
    Generate the statistical summary JSON with exact schema:
    {
      "p_value": float,
      "effect_size": { "cohen_d": float },
      "degradation_percent": float,
      "boundary_threshold": float,
      "regression_slope": float,
      "r_squared": float
    }
    """
    # Load data
    logs = load_exploration_logs()
    scores_map = load_scores_map()
    
    # Separate baseline and lite metrics for t-test
    # Assuming logs contain both baseline and lite metrics for paired comparison
    baseline_metrics = []
    lite_metrics = []
    all_scores = []
    all_metrics = []
    
    for log in logs:
        repo_id = log.get('repo_id')
        if not repo_id:
            continue
        
        # Extract metrics - adjust based on actual log structure from T023
        # Assuming log contains 'baseline_context_precision' and 'context_precision' (lite)
        baseline_val = log.get('baseline_context_precision')
        lite_val = log.get('context_precision')
        
        if baseline_val is not None and lite_val is not None:
            baseline_metrics.append(float(baseline_val))
            lite_metrics.append(float(lite_val))
        
        if repo_id in scores_map:
            all_scores.append(scores_map[repo_id])
            if lite_val is not None:
                all_metrics.append(float(lite_val))
    
    # 1. P-value and test type
    p_value, test_name = run_ttest(baseline_metrics, lite_metrics)
    
    # 2. Effect size (Cohen's d)
    cohen_d = calculate_effect_size(baseline_metrics, lite_metrics)
    
    # 3. Degradation percent (for irregular set)
    # First find threshold
    if all_scores and all_metrics:
        boundary_threshold = find_threshold(all_scores, all_metrics)
    else:
        boundary_threshold = 0.5
    
    degradation_percent = calculate_performance_degradation_irregular(
        scores_map, logs, threshold=boundary_threshold
    )
    
    # 4. Regression analysis (slope, r_squared)
    slope, r_squared = calculate_regression_analysis(scores_map, logs)
    
    summary = {
        "p_value": float(p_value),
        "effect_size": {
            "cohen_d": float(cohen_d)
        },
        "degradation_percent": float(degradation_percent),
        "boundary_threshold": float(boundary_threshold),
        "regression_slope": float(slope),
        "r_squared": float(r_squared)
    }
    
    return summary

def main():
    """Main entry point to generate statistical summary and write to file."""
    ensure_directories()
    summary = generate_statistical_summary()
    
    output_path = get_path("results", "statistical_summary.json")
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Statistical summary written to {output_path}")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()