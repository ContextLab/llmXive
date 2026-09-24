"""
Pairwise comparisons script for User Story 2.
Implements Bonferroni-corrected and FDR-corrected t-tests with effect sizes (Cohen's d)
and confidence intervals via bootstrapping.
"""
import os
import sys
import json
import argparse
import warnings
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path

# Ensure project root is in path
def get_project_root():
    """Get the project root directory."""
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    return project_root

sys.path.insert(0, str(get_project_root()))

def load_wide_data(input_path):
    """
    Load wide-format data from CSV.
    Expected columns: participant_id, Professional_cred, Minimalist_cred, Low-Quality_cred, Neutral_cred,
                      Professional_prof, Minimalist_prof, Low-Quality_prof, Neutral_prof
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    df = pd.read_csv(input_path)
    return df

def calculate_cohens_d(group1, group2):
    """
    Calculate Cohen's d for two related samples (paired).
    d = (mean1 - mean2) / std_diff
    """
    mean_diff = np.mean(group1) - np.mean(group2)
    std_diff = np.std(group1 - group2, ddof=1)
    if std_diff == 0:
        return 0.0
    return mean_diff / std_diff

def bootstrap_cohens_d(group1, group2, n_iterations=1000, seed=42):
    """
    Calculate Cohen's d with bootstrapped confidence intervals.
    Resamples participants (rows) with replacement.
    """
    np.random.seed(seed)
    n = len(group1)
    bootstrap_dists = []

    for _ in range(n_iterations):
        # Resample indices with replacement
        indices = np.random.choice(n, size=n, replace=True)
        g1_boot = group1[indices]
        g2_boot = group2[indices]
        d_boot = calculate_cohens_d(g1_boot, g2_boot)
        bootstrap_dists.append(d_boot)

    bootstrap_dists = np.array(bootstrap_dists)
    mean_d = np.mean(bootstrap_dists)
    ci_lower = np.percentile(bootstrap_dists, 2.5)
    ci_upper = np.percentile(bootstrap_dists, 97.5)

    return {
        "cohen_d": mean_d,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "n_iterations": n_iterations
    }

def apply_bonferroni(p_value, n_comparisons):
    """Apply Bonferroni correction."""
    corrected = p_value * n_comparisons
    return min(corrected, 1.0)

def apply_fdr_bh(p_values):
    """Apply Benjamini-Hochberg FDR correction."""
    p_values = np.array(p_values)
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]

    ranks = np.arange(1, n + 1)
    fdr_corrected = (sorted_p * n) / ranks
    fdr_corrected = np.minimum(fdr_corrected, 1.0)
    fdr_corrected = np.maximum(np.cummin(fdr_corrected[::-1])[::-1], 0)

    # Restore original order
    result = np.empty(n)
    result[sorted_indices] = fdr_corrected
    return result

def run_pairwise_tests_with_effects(df, correction_method="bonferroni"):
    """
    Run pairwise t-tests between conditions with effect sizes and CIs.
    Conditions: Professional, Minimalist, Low-Quality, Neutral
    Metrics: credibility, professionalism
    """
    conditions = ["Professional", "Minimalist", "Low-Quality", "Neutral"]
    metrics = ["cred", "prof"]
    comparisons = []

    # Generate all unique pairs
    pair_indices = []
    for i in range(len(conditions)):
        for j in range(i + 1, len(conditions)):
            pair_indices.append((i, j))

    n_comparisons = len(pair_indices)

    for metric in metrics:
        for idx_i, idx_j in pair_indices:
            cond_i = conditions[idx_i]
            cond_j = conditions[idx_j]

            col_i = f"{cond_i}_{metric}"
            col_j = f"{cond_j}_{metric}"

            # Drop NaNs for this pair
            valid_mask = df[[col_i, col_j]].notna().all(axis=1)
            if valid_mask.sum() < 2:
                continue

            group_i = df.loc[valid_mask, col_i].values
            group_j = df.loc[valid_mask, col_j].values

            # Paired t-test
            t_stat, p_val = stats.ttest_rel(group_i, group_j)

            # Effect size
            cohens_d_result = bootstrap_cohens_d(group_i, group_j, n_iterations=1000, seed=42)

            # Corrections
            bonf_p = apply_bonferroni(p_val, n_comparisons)
            fdr_p = apply_fdr_bh([p_val])[0]

            comparisons.append({
                "metric": metric,
                "condition_1": cond_i,
                "condition_2": cond_j,
                "t_statistic": float(t_stat),
                "p_value_unadjusted": float(p_val),
                "p_value_bonferroni": float(bonf_p),
                "p_value_fdr": float(fdr_p),
                "cohen_d": float(cohens_d_result["cohen_d"]),
                "ci_lower": float(cohens_d_result["ci_lower"]),
                "ci_upper": float(cohens_d_result["ci_upper"]),
                "n_iterations": cohens_d_result["n_iterations"],
                "n_participants": int(valid_mask.sum())
            })

    return comparisons

def main():
    parser = argparse.ArgumentParser(description="Run pairwise comparisons with bootstrapped effect sizes.")
    parser.add_argument("--input", type=str, required=True, help="Path to wide-format CSV")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON")
    parser.add_argument("--correction-method", type=str, choices=["bonferroni", "fdr"], default="bonferroni",
                        help="Correction method for p-values")
    args = parser.parse_args()

    print(f"Loading data from {args.input}...")
    df = load_wide_data(args.input)

    print(f"Running pairwise tests with {args.correction_method} correction...")
    results = run_pairwise_tests_with_effects(df, correction_method=args.correction_method)

    output_data = {
        "correction_method": args.correction_method,
        "n_comparisons": len(results),
        "pairwise_results": results
    }

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"Results saved to {args.output}")

if __name__ == "__main__":
    main()