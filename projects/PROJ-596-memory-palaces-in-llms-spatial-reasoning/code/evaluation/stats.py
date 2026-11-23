import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from scipy import stats

def load_recall_results(path: str) -> Dict[str, List[float]]:
    """Load recall results from a JSON file."""
    with open(path, 'r') as f:
        data = json.load(f)
    return data

def check_normality(data: List[float]) -> Tuple[bool, float]:
    """Check if data is normally distributed using Shapiro-Wilk test."""
    if len(data) < 3:
        return False, 1.0
    stat, p_value = stats.shapiro(data)
    return p_value > 0.05, p_value

def perform_paired_ttest(data1: List[float], data2: List[float]) -> Tuple[float, float]:
    """Perform paired t-test."""
    t_stat, p_value = stats.ttest_rel(data1, data2)
    return t_stat, p_value

def perform_wilcoxon_signed_rank(data1: List[float], data2: List[float]) -> Tuple[float, float]:
    """Perform Wilcoxon signed-rank test."""
    stat, p_value = stats.wilcoxon(data1, data2)
    return stat, p_value

def compute_cohens_d(data1: List[float], data2: List[float]) -> float:
    """Compute Cohen's d."""
    n1, n2 = len(data1), len(data2)
    mean1, mean2 = np.mean(data1), np.mean(data2)
    std1, std2 = np.std(data1), np.std(data2)
    pooled_std = np.sqrt((std1**2 + std2**2) / 2)
    if pooled_std == 0:
        return 0.0
    return (mean1 - mean2) / pooled_std

def compute_cohens_d_confidence_interval(data1: List[float], data2: List[float], confidence=0.95) -> Tuple[float, float]:
    """Compute confidence interval for Cohen's d."""
    # Simplified implementation
    d = compute_cohens_d(data1, data2)
    n = len(data1)
    se = np.sqrt((1/n) + (d**2 / (2*n)))
    z = stats.norm.ppf((1 + confidence) / 2)
    ci_low = d - z * se
    ci_high = d + z * se
    return ci_low, ci_high

def get_cohen_interpretation(d: float) -> str:
    """Interpret Cohen's d."""
    if abs(d) < 0.2:
        return "negligible"
    elif abs(d) < 0.5:
        return "small"
    elif abs(d) < 0.8:
        return "medium"
    else:
        return "large"

def run_analysis_for_dataset(dataset_name: str, spatial_data: List[float], baseline_data: List[float]) -> Dict[str, Any]:
    """Run statistical analysis for a dataset."""
    normal_spatial, p_spatial = check_normality(spatial_data)
    normal_baseline, p_baseline = check_normality(baseline_data)
    
    # Choose test
    if normal_spatial and normal_baseline:
        t_stat, p_value = perform_paired_ttest(spatial_data, baseline_data)
        test_name = "paired_ttest"
    else:
        t_stat, p_value = perform_wilcoxon_signed_rank(spatial_data, baseline_data)
        test_name = "wilcoxon"
    
    cohen_d = compute_cohens_d(spatial_data, baseline_data)
    ci_low, ci_high = compute_cohens_d_confidence_interval(spatial_data, baseline_data)
    interpretation = get_cohen_interpretation(cohen_d)
    
    return {
        "dataset": dataset_name,
        "test": test_name,
        "p_value": p_value,
        "cohen_d": cohen_d,
        "cohen_d_ci": [ci_low, ci_high],
        "interpretation": interpretation
    }

def run_all_analyses(results_path: str) -> List[Dict[str, Any]]:
    """Run analyses for all datasets."""
    # This would load results and run analysis for each dataset
    pass

def save_analysis_results(results: List[Dict[str, Any]], output_path: str):
    """Save analysis results to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def main():
    # Example usage
    pass
