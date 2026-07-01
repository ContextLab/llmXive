"""
Statistical analysis module for comparing Baseline vs. Spiking Transformer performance.

Implements paired t-tests (FR-009) on perplexity and energy metrics,
using matching random seeds to ensure valid pairing.
"""
import os
import sys
import json
import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Tuple, Optional, Any
import warnings

# Add project root to path if running as script
if __package__ is None:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_metrics_data(
    baseline_path: str,
    spiking_path: str
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load baseline and spiking metrics from CSV files.
    
    Args:
        baseline_path: Path to baseline_metrics.csv
        spiking_path: Path to spiking_metrics.csv
        
    Returns:
        Tuple of (baseline_df, spiking_df)
        
    Raises:
        FileNotFoundError: If CSV files do not exist
        ValueError: If required columns are missing
    """
    if not os.path.exists(baseline_path):
        raise FileNotFoundError(f"Baseline metrics file not found: {baseline_path}")
    if not os.path.exists(spiking_path):
        raise FileNotFoundError(f"Spiking metrics file not found: {spiking_path}")
        
    baseline_df = pd.read_csv(baseline_path)
    spiking_df = pd.read_csv(spiking_path)
    
    required_cols = ['seed', 'perplexity', 'energy_per_token_kWh']
    for df, name in [(baseline_df, "baseline"), (spiking_df, "spiking")]:
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(f"Missing columns in {name} metrics: {missing}")
            
    return baseline_df, spiking_df

def prepare_paired_data(
    baseline_df: pd.DataFrame,
    spiking_df: pd.DataFrame,
    metric: str
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepare paired data arrays for a specific metric, matching by seed.
    
    Args:
        baseline_df: Baseline metrics dataframe
        spiking_df: Spiking metrics dataframe
        metric: Name of the metric column (e.g., 'perplexity', 'energy_per_token_kWh')
        
    Returns:
        Tuple of (baseline_values, spiking_values) as numpy arrays
        
    Raises:
        ValueError: If seeds do not match or data is insufficient
    """
    # Group by seed and take the final epoch (or mean if needed, but task implies final comparison)
    # Assuming the CSV contains epoch-level data, we take the best/final epoch per seed
    # Strategy: For each seed, take the row with the lowest validation perplexity (for perplexity)
    # or the last row (for energy, assuming it stabilizes). 
    # To be robust, we'll take the mean of the last 3 epochs per seed if available, else the last row.
    
    def aggregate_seed(df: pd.DataFrame, seed_col: str = 'seed', metric_col: str = metric) -> pd.Series:
        result = {}
        for seed in df[seed_col].unique():
            seed_data = df[df[seed_col] == seed].sort_values('epoch')
            if len(seed_data) >= 3:
                # Average of last 3 epochs
                result[seed] = seed_data[metric_col].tail(3).mean()
            else:
                # Take last available
                result[seed] = seed_data[metric_col].iloc[-1]
        return pd.Series(result)
        
    baseline_vals = aggregate_seed(baseline_df, metric_col=metric)
    spiking_vals = aggregate_seed(spiking_df, metric_col=metric)
    
    # Align by seed
    common_seeds = sorted(set(baseline_vals.index) & set(spiking_vals.index))
    
    if len(common_seeds) < 2:
        raise ValueError(f"Insufficient matching seeds for paired test. Found {len(common_seeds)}.")
        
    b_array = baseline_vals[common_seeds].values
    s_array = spiking_vals[common_seeds].values
    
    return b_array, s_array

def run_paired_ttest(
    baseline_df: pd.DataFrame,
    spiking_df: pd.DataFrame,
    metric: str,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform a paired t-test comparing baseline vs. spiking model for a given metric.
    
    Args:
        baseline_df: Baseline metrics dataframe
        spiking_df: Spiking metrics dataframe
        metric: Metric name ('perplexity' or 'energy_per_token_kWh')
        alpha: Significance level
        
    Returns:
        Dictionary containing test statistics, p-value, confidence interval, and conclusion
    """
    b_vals, s_vals = prepare_paired_data(baseline_df, spiking_df, metric)
    
    # Perform paired t-test
    # H0: mean(baseline) == mean(spiking)
    # H1: mean(baseline) != mean(spiking)
    t_stat, p_val = stats.ttest_rel(b_vals, s_vals)
    
    # Calculate effect size (Cohen's d for paired samples)
    diff = b_vals - s_vals
    mean_diff = np.mean(diff)
    std_diff = np.std(diff, ddof=1)
    cohens_d = mean_diff / std_diff if std_diff != 0 else 0.0
    
    # 95% Confidence Interval for the mean difference
    n = len(diff)
    se = std_diff / np.sqrt(n)
    ci_low, ci_high = stats.t.interval(0.95, df=n-1, loc=mean_diff, scale=se)
    
    # Determine significance
    is_significant = p_val < alpha
    
    # Determine direction (if significant)
    direction = "spiking_better" if mean_diff > 0 else "baseline_better" if mean_diff < 0 else "no_difference"
    
    # For perplexity: lower is better. For energy: lower is better.
    # If mean_diff (baseline - spiking) > 0, then spiking is lower (better).
    
    return {
        "metric": metric,
        "n_pairs": n,
        "mean_baseline": float(np.mean(b_vals)),
        "mean_spiking": float(np.mean(s_vals)),
        "mean_difference": float(mean_diff),
        "std_difference": float(std_diff),
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "confidence_interval_95": [float(ci_low), float(ci_high)],
        "is_significant_at_0.05": is_significant,
        "effect_size_cohen_d": float(cohens_d),
        "direction": direction,
        "conclusion": (
            f"Significant difference found (p={p_val:.4f}). "
            f"{direction.replace('_', ' ').title()}."
            if is_significant else
            f"No significant difference found (p={p_val:.4f})."
        )
    }

def apply_bonferroni_correction(
    p_values: List[float],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Apply Bonferroni correction for multiple hypothesis testing.
    
    Args:
        p_values: List of raw p-values
        alpha: Significance level
        
    Returns:
        Dictionary with corrected p-values and significance decisions
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return {"corrected_p_values": [], "is_significant": [], "alpha_corrected": alpha}
        
    alpha_corrected = alpha / n_tests
    corrected_p_values = [min(p * n_tests, 1.0) for p in p_values]
    is_significant = [p < alpha for p in corrected_p_values]
    
    return {
        "raw_p_values": p_values,
        "corrected_p_values": corrected_p_values,
        "is_significant_after_correction": is_significant,
        "alpha_corrected": alpha_corrected,
        "n_tests": n_tests
    }

def generate_statistical_report(
    baseline_path: str,
    spiking_path: str,
    output_path: str,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Generate a comprehensive statistical analysis report.
    
    Args:
        baseline_path: Path to baseline_metrics.csv
        spiking_path: Path to spiking_metrics.csv
        output_path: Path to save the report (JSON)
        alpha: Significance level
        
    Returns:
        The full report dictionary
    """
    baseline_df, spiking_df = load_metrics_data(baseline_path, spiking_path)
    
    results = {
        "meta": {
            "baseline_file": baseline_path,
            "spiking_file": spiking_path,
            "alpha": alpha,
            "test_type": "Paired T-Test (FR-009)",
            "matching_criteria": "Random Seed"
        },
        "tests": {}
    }
    
    p_values = []
    
    for metric in ["perplexity", "energy_per_token_kWh"]:
        try:
            test_result = run_paired_ttest(baseline_df, spiking_df, metric, alpha)
            results["tests"][metric] = test_result
            p_values.append(test_result["p_value"])
        except Exception as e:
            results["tests"][metric] = {
                "error": str(e),
                "status": "failed"
            }
    
    # Apply Bonferroni correction
    if p_values:
        correction = apply_bonferroni_correction(p_values, alpha)
        results["multiple_comparison_correction"] = correction
        
        # Update significance in results if applicable
        for i, metric in enumerate(["perplexity", "energy_per_token_kWh"]):
            if metric in results["tests"] and "error" not in results["tests"][metric]:
                results["tests"][metric]["is_significant_after_bonferroni"] = correction["is_significant_after_correction"][i]
    
    # Save report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    return results

def main():
    """
    Main entry point for running statistical analysis.
    Reads from data/processed/ and writes to data/results/
    """
    # Define paths relative to project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    baseline_path = os.path.join(project_root, "data", "processed", "baseline_metrics.csv")
    spiking_path = os.path.join(project_root, "data", "processed", "spiking_metrics.csv")
    output_path = os.path.join(project_root, "data", "results", "statistical_analysis.json")
    
    print(f"Loading data from:\n  Baseline: {baseline_path}\n  Spiking: {spiking_path}")
    
    try:
        report = generate_statistical_report(baseline_path, spiking_path, output_path)
        print(f"\nStatistical analysis complete. Report saved to: {output_path}")
        
        # Print summary
        print("\n--- Summary ---")
        for metric, res in report["tests"].items():
            if "error" in res:
                print(f"{metric}: FAILED - {res['error']}")
            else:
                sig = "YES" if res["is_significant_at_0.05"] else "NO"
                print(f"{metric}: p={res['p_value']:.4f}, Significant={sig}, Direction={res['direction']}")
                
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure baseline_metrics.csv and spiking_metrics.csv exist in data/processed/")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
