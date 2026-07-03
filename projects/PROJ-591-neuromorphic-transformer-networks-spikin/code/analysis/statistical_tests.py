import os
import sys
import json
import pandas as pd
import numpy as np
from scipy import stats
from typing import List, Dict, Tuple, Optional, Any

def load_metrics_data(filepath: str) -> pd.DataFrame:
    """
    Load metrics from a CSV file.
    Expected columns: seed, epoch, perplexity, energy_per_token_kWh, wall_clock_time, temporal_coding_metrics (optional)
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Metrics file not found: {filepath}")
    df = pd.read_csv(filepath)
    return df

def prepare_paired_data(baseline_df: pd.DataFrame, spiking_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepare paired data for statistical testing by matching on 'seed'.
    Returns the latest epoch metrics for each seed to ensure a single comparison point per seed.
    """
    # Get the latest epoch for each seed
    baseline_latest = baseline_df.sort_values('epoch').groupby('seed').last().reset_index()
    spiking_latest = spiking_df.sort_values('epoch').groupby('seed').last().reset_index()

    # Merge on seed to ensure pairing
    paired = pd.merge(baseline_latest, spiking_latest, on='seed', suffixes=('_baseline', '_spiking'))

    if paired.empty:
        raise ValueError("No matching seeds found between baseline and spiking datasets.")

    return baseline_latest, spiking_latest, paired

def run_paired_ttest(baseline_vals: np.ndarray, spiking_vals: np.ndarray) -> Dict[str, Any]:
    """
    Perform a paired t-test on two arrays of values.
    Returns a dictionary with t-statistic, p-value, and confidence interval.
    """
    if len(baseline_vals) != len(spiking_vals):
        raise ValueError("Arrays must be of equal length for paired t-test.")
    if len(baseline_vals) < 2:
        raise ValueError("At least 2 samples are required for a t-test.")

    t_stat, p_val = stats.ttest_rel(baseline_vals, spiking_vals)
    
    # Calculate 95% confidence interval of the difference
    diff = baseline_vals - spiking_vals
    n = len(diff)
    mean_diff = np.mean(diff)
    std_err = stats.sem(diff)
    conf_int = stats.t.interval(0.95, n - 1, loc=mean_diff, scale=std_err)

    return {
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "mean_difference": float(mean_diff),
        "confidence_interval_95": [float(conf_int[0]), float(conf_int[1])],
        "n_pairs": n
    }

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Bonferroni and Holm-Bonferroni corrections to a list of p-values.
    
    Args:
        p_values: List of raw p-values from hypothesis tests.
        alpha: Significance level (default 0.05).
    
    Returns:
        Dictionary containing corrected p-values and significance flags.
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return {
            "bonferroni_corrected": [],
            "holm_corrected": [],
            "bonferroni_significant": [],
            "holm_significant": []
        }

    # Bonferroni Correction
    # Corrected p-value = raw p-value * n_tests
    # Significance if p_corrected < alpha
    bonf_corrected = [min(p * n_tests, 1.0) for p in p_values]
    bonf_significant = [p < alpha for p in bonf_corrected]

    # Holm-Bonferroni Correction
    # Sort p-values, compare with alpha / (n - i)
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_indices]
    
    holm_corrected = np.zeros(n_tests)
    holm_significant = np.zeros(n_tests, dtype=bool)
    
    cumulative_max = 0.0
    for i in range(n_tests):
        # The adjusted p-value is the maximum of the previous adjusted p-value 
        # and the current raw p-value * (n - i)
        # But for the simple Holm procedure (step-down):
        # We check if p_(i) < alpha / (n - i + 1). If not, stop.
        # However, to return corrected p-values (adjusted p-values), we use:
        # p_adj(i) = max(p_adj(i-1), p_(i) * (n - i + 1))
        
        # Calculate raw adjusted value for this step
        adj_val = sorted_p[i] * (n_tests - i)
        cumulative_max = max(cumulative_max, adj_val)
        holm_corrected[sorted_indices[i]] = min(cumulative_max, 1.0)
        
        # Significance check for Holm
        # p < alpha / (n - i)
        threshold = alpha / (n_tests - i)
        if sorted_p[i] < threshold:
            holm_significant[sorted_indices[i]] = True
        else:
            # Once one fails, all subsequent (larger p-values) also fail in step-down
            # But we continue to fill the array for correctness of the algorithm
            pass
    
    # Re-evaluate Holm significance strictly: 
    # If a test is significant, all tests with smaller raw p-values must also be significant.
    # The boolean array above is already correct because we iterate from smallest p.
    # However, if p[i] >= alpha/(n-i), then p[i] and all larger p-values are not significant.
    # The loop above sets significant=True only if the condition holds. 
    # We need to ensure that if a step fails, subsequent ones are False.
    # The logic `if sorted_p[i] < threshold` sets True. If it fails, it remains False (initialized).
    # But we must ensure that if index i fails, index i+1 (which has larger p) also fails.
    # Since we iterate i from 0 to n-1, if sorted_p[i] >= threshold, we just don't set True.
    # But we don't explicitly break. The initialization is False, so it stays False. Correct.

    return {
        "bonferroni_corrected": bonf_corrected,
        "holm_corrected": holm_corrected.tolist(),
        "bonferroni_significant": bonf_significant,
        "holm_significant": holm_significant.tolist()
    }

def generate_statistical_report(baseline_path: str, spiking_path: str, output_path: str):
    """
    Generate a comprehensive statistical analysis report comparing baseline and spiking models.
    Includes paired t-tests for perplexity and energy, with multiple comparison corrections.
    """
    # Load data
    baseline_df = load_metrics_data(baseline_path)
    spiking_df = load_metrics_data(spiking_path)

    # Prepare paired data
    baseline_latest, spiking_latest, paired_df = prepare_paired_data(baseline_df, spiking_df)

    # Extract metrics for testing
    perplexity_baseline = paired_df['perplexity_baseline'].values
    perplexity_spiking = paired_df['perplexity_spiking'].values
    energy_baseline = paired_df['energy_per_token_kWh_baseline'].values
    energy_spiking = paired_df['energy_per_token_kWh_spiking'].values

    # Run paired t-tests
    ttest_perplexity = run_paired_ttest(perplexity_baseline, perplexity_spiking)
    ttest_energy = run_paired_ttest(energy_baseline, energy_spiking)

    # Collect raw p-values for correction
    raw_p_values = [ttest_perplexity['p_value'], ttest_energy['p_value']]
    test_names = ['Perplexity', 'Energy_per_token']

    # Apply corrections
    corrections = apply_bonferroni_correction(raw_p_values)

    # Build report structure
    report = {
        "summary": {
            "n_seeds": int(ttest_perplexity['n_pairs']),
            "metrics_tested": len(raw_p_values),
            "method": "Paired t-test with Bonferroni and Holm-Bonferroni correction"
        },
        "results": {
            "perplexity": {
                "t_statistic": ttest_perplexity['t_statistic'],
                "p_value_raw": ttest_perplexity['p_value'],
                "mean_difference": ttest_perplexity['mean_difference'],
                "ci_95": ttest_perplexity['confidence_interval_95'],
                "bonferroni_corrected_p": corrections['bonferroni_corrected'][0],
                "holm_corrected_p": corrections['holm_corrected'][0],
                "is_significant_bonferroni": corrections['bonferroni_significant'][0],
                "is_significant_holm": corrections['holm_significant'][0]
            },
            "energy": {
                "t_statistic": ttest_energy['t_statistic'],
                "p_value_raw": ttest_energy['p_value'],
                "mean_difference": ttest_energy['mean_difference'],
                "ci_95": ttest_energy['confidence_interval_95'],
                "bonferroni_corrected_p": corrections['bonferroni_corrected'][1],
                "holm_corrected_p": corrections['holm_corrected'][1],
                "is_significant_bonferroni": corrections['bonferroni_significant'][1],
                "is_significant_holm": corrections['holm_significant'][1]
            }
        },
        "corrections_applied": {
            "method": ["Bonferroni", "Holm-Bonferroni"],
            "raw_p_values": raw_p_values,
            "test_names": test_names,
            "corrected_p_values": corrections['bonferroni_corrected'],
            "holm_corrected_p_values": corrections['holm_corrected'],
            "significance_threshold": 0.05
        }
    }

    # Write report to JSON (and potentially markdown later)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Also generate a markdown summary
    md_path = output_path.replace('.json', '.md')
    with open(md_path, 'w') as f:
        f.write("# Statistical Analysis Report\n\n")
        f.write(f"## Summary\n")
        f.write(f"- **Number of Seeds**: {report['summary']['n_seeds']}\n")
        f.write(f"- **Metrics Tested**: {report['summary']['metrics_tested']}\n")
        f.write(f"- **Method**: {report['summary']['method']}\n\n")
        
        f.write("## Results\n\n")
        f.write("### Perplexity Comparison\n")
        f.write(f"- Mean Difference (Baseline - Spiking): {report['results']['perplexity']['mean_difference']:.4f}\n")
        f.write(f"- Raw p-value: {report['results']['perplexity']['p_value_raw']:.6f}\n")
        f.write(f"- Bonferroni Corrected p-value: {report['results']['perplexity']['bonferroni_corrected_p']:.6f}\n")
        f.write(f"- Holm Corrected p-value: {report['results']['perplexity']['holm_corrected_p']:.6f}\n")
        f.write(f"- Significant (Bonferroni): {report['results']['perplexity']['is_significant_bonferroni']}\n")
        f.write(f"- Significant (Holm): {report['results']['perplexity']['is_significant_holm']}\n\n")
        
        f.write("### Energy Comparison\n")
        f.write(f"- Mean Difference (Baseline - Spiking): {report['results']['energy']['mean_difference']:.6f} kWh\n")
        f.write(f"- Raw p-value: {report['results']['energy']['p_value_raw']:.6f}\n")
        f.write(f"- Bonferroni Corrected p-value: {report['results']['energy']['bonferroni_corrected_p']:.6f}\n")
        f.write(f"- Holm Corrected p-value: {report['results']['energy']['holm_corrected_p']:.6f}\n")
        f.write(f"- Significant (Bonferroni): {report['results']['energy']['is_significant_bonferroni']}\n")
        f.write(f"- Significant (Holm): {report['results']['energy']['is_significant_holm']}\n\n")
        
        f.write("## Multiple Comparison Correction Details\n")
        f.write(f"Raw p-values: {raw_p_values}\n")
        f.write(f"Bonferroni Corrected: {corrections['bonferroni_corrected']}\n")
        f.write(f"Holm Corrected: {corrections['holm_corrected']}\n")

    print(f"Statistical report generated: {output_path}")
    print(f"Markdown summary generated: {md_path}")

def main():
    """
    Entry point for running the statistical analysis.
    Expects environment variables or arguments to locate input CSVs.
    """
    baseline_path = "data/processed/baseline_metrics.csv"
    spiking_path = "data/processed/spiking_metrics.csv"
    output_path = "data/results/statistical_analysis.json"

    # Check if input files exist
    if not os.path.exists(baseline_path) or not os.path.exists(spiking_path):
        print("Error: Required input files not found.")
        print(f"Expected: {baseline_path}, {spiking_path}")
        sys.exit(1)

    generate_statistical_report(baseline_path, spiking_path, output_path)

if __name__ == "__main__":
    main()