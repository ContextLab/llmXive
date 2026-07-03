import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from scipy import stats

from evaluation.metrics import compute_exact_match_recall, evaluate_model_on_dataset, run_evaluation_for_seed, aggregate_results_by_seed, main

def load_recall_results(results_dir: Path) -> Dict[str, Dict[str, List[float]]]:
    """
    Load recall accuracy results from the artifacts/results directory.
    Expected structure:
    {
        "dataset_name": {
            "spatial": [acc1, acc2, ...],
            "baseline": [acc1, acc2, ...]
        }
    }
    """
    recall_file = results_dir / "recall_accuracy.json"
    if not recall_file.exists():
        raise FileNotFoundError(f"Recall results file not found: {recall_file}")
    
    with open(recall_file, 'r') as f:
        return json.load(f)

def check_normality(data: List[float]) -> Tuple[bool, float]:
    """
    Perform Shapiro-Wilk test for normality.
    Returns (is_normal, p_value).
    """
    if len(data) < 3:
        return True, 1.0  # Not enough data to reject normality
    
    stat, p_value = stats.shapiro(data)
    return p_value > 0.05, p_value

def perform_paired_ttest(sample1: List[float], sample2: List[float]) -> Tuple[float, float]:
    """
    Perform paired two-tailed t-test.
    Returns (t_statistic, p_value).
    """
    t_stat, p_value = stats.ttest_rel(sample1, sample2)
    return t_stat, p_value

def perform_wilcoxon_signed_rank(sample1: List[float], sample2: List[float]) -> Tuple[float, float]:
    """
    Perform Wilcoxon signed-rank test (non-parametric alternative).
    Returns (z_statistic, p_value).
    """
    stat, p_value = stats.wilcoxon(sample1, sample2)
    return stat, p_value

def compute_cohens_d(sample1: List[float], sample2: List[float]) -> float:
    """
    Compute Cohen's d effect size for paired samples.
    d = mean(diff) / std(diff)
    """
    if len(sample1) != len(sample2):
        raise ValueError("Samples must be of equal length for paired effect size.")
    
    diffs = np.array(sample1) - np.array(sample2)
    mean_diff = np.mean(diffs)
    std_diff = np.std(diffs, ddof=1)
    
    if std_diff == 0:
        return 0.0
    
    return mean_diff / std_diff

def compute_cohens_d_confidence_interval(sample1: List[float], sample2: List[float], confidence: float = 0.95) -> Tuple[float, float, float]:
    """
    Compute Cohen's d with 95% confidence interval.
    Uses the non-central t-distribution approximation for the CI.
    
    Returns (cohens_d, lower_ci, upper_ci).
    """
    if len(sample1) != len(sample2):
        raise ValueError("Samples must be of equal length for paired effect size.")
    
    n = len(sample1)
    diffs = np.array(sample1) - np.array(sample2)
    mean_diff = np.mean(diffs)
    std_diff = np.std(diffs, ddof=1)
    
    if std_diff == 0:
        return 0.0, 0.0, 0.0
    
    d = mean_diff / std_diff
    
    # Approximate standard error for Cohen's d
    # SE_d ≈ sqrt((n / (n-1)) + (d^2 / (2*n)))
    se_d = np.sqrt((n / (n - 1)) + (d**2 / (2 * n)))
    
    # Critical t-value
    alpha = 1 - confidence
    df = n - 1
    t_crit = stats.t.ppf(1 - alpha/2, df)
    
    lower_ci = d - t_crit * se_d
    upper_ci = d + t_crit * se_d
    
    return d, lower_ci, upper_ci

def get_cohen_interpretation(d: float) -> str:
    """
    Interpret the magnitude of Cohen's d.
    """
    abs_d = abs(d)
    if abs_d < 0.2:
        return "negligible"
    elif abs_d < 0.5:
        return "small"
    elif abs_d < 0.8:
        return "medium"
    else:
        return "large"

def run_analysis_for_dataset(
    dataset_name: str,
    spatial_results: List[float],
    baseline_results: List[float]
) -> Dict[str, Any]:
    """
    Perform full statistical analysis for a single dataset comparison.
    Includes normality check, test selection, p-value, effect size, and CI.
    """
    analysis = {
        "dataset": dataset_name,
        "n_samples": len(spatial_results),
        "spatial_mean": float(np.mean(spatial_results)),
        "baseline_mean": float(np.mean(baseline_results)),
    }

    # Check normality
    is_normal_spatial, p_spatial = check_normality(spatial_results)
    is_normal_baseline, p_baseline = check_normality(baseline_results)
    analysis["normality_check"] = {
        "spatial": {"is_normal": is_normal_spatial, "p_value": float(p_spatial)},
        "baseline": {"is_normal": is_normal_baseline, "p_value": float(p_baseline)}
    }

    # Select test
    use_ttest = is_normal_spatial and is_normal_baseline
    if use_ttest:
        t_stat, p_val = perform_paired_ttest(spatial_results, baseline_results)
        test_name = "paired_ttest"
    else:
        stat, p_val = perform_wilcoxon_signed_rank(spatial_results, baseline_results)
        test_name = "wilcoxon_signed_rank"
        t_stat = None

    analysis["test_used"] = test_name
    analysis["p_value"] = float(p_val)
    if t_stat is not None:
        analysis["t_statistic"] = float(t_stat)
    else:
        analysis["wilcoxon_statistic"] = float(stat)

    # Effect size
    d, lower_ci, upper_ci = compute_cohens_d_confidence_interval(spatial_results, baseline_results)
    analysis["effect_size"] = {
        "cohens_d": float(d),
        "interpretation": get_cohen_interpretation(d),
        "confidence_interval_95": {
            "lower": float(lower_ci),
            "upper": float(upper_ci)
        }
    }

    return analysis

def run_all_analyses(results_dir: Path) -> Dict[str, Any]:
    """
    Run statistical analysis for all datasets found in recall_accuracy.json.
    Returns a dictionary with results for each dataset.
    """
    raw_results = load_recall_results(results_dir)
    all_analyses = {}

    for dataset_name, data in raw_results.items():
        spatial = data.get("spatial", [])
        baseline = data.get("baseline", [])
        
        if not spatial or not baseline:
            continue
        
        all_analyses[dataset_name] = run_analysis_for_dataset(dataset_name, spatial, baseline)

    return all_analyses

def save_analysis_results(results: Dict[str, Any], output_path: Path) -> None:
    """
    Save analysis results to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def main():
    """
    Main entry point for statistical analysis.
    """
    results_dir = Path("artifacts/results")
    output_file = results_dir / "statistical_analysis_results.json"
    
    if not results_dir.exists():
        print(f"Error: Results directory not found: {results_dir}")
        return
    
    try:
        results = run_all_analyses(results_dir)
        save_analysis_results(results, output_file)
        print(f"Statistical analysis complete. Results saved to: {output_file}")
    except Exception as e:
        print(f"Error during analysis: {e}")
        raise

if __name__ == "__main__":
    main()