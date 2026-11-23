import argparse
import json
import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats

# Ensure we can import from the project root if run as a script
# but rely on the provided API surface for imports.
# The task requires implementing the Secondary Path (Spec FR-005 Decision Tree).

def log_decision_tree_step(step_name, message, results):
    """Helper to log a step in the decision tree."""
    logging.info(f"[Decision Tree] {step_name}: {message}")
    results["steps"].append({
        "step": step_name,
        "message": message,
        "details": results.get("details", {})
    })

def run_secondary_decision_tree(data_path, output_path):
    """
    Implements the Secondary Path: Spec FR-005 Dynamic Decision Tree.
    
    Logic:
    1. Load cleaned data (data/processed/cleaned_dataset.csv).
    2. Check homogeneity of variance (Levene's Test).
    3. Check normality (Shapiro-Wilk).
    4. Select test based on assumptions:
       - Normal + Equal Variance -> Standard ANOVA
       - Normal + Unequal Variance -> Welch's ANOVA
       - Non-Normal -> Welch-James (or Kruskal-Wallis if appropriate, 
         but Plan specifies Welch-James for non-normal in this context).
    5. Output results to data/reports/sensitivity_decision_tree_results.json.
    
    Note: This is a SENSITIVITY ANALYSIS. The PRIMARY analysis (T036a) 
    uses Pre-specified Welch's ANOVA regardless of assumptions.
    """
    
    results = {
        "methodology": "Spec FR-005 Dynamic Decision Tree (Sensitivity Analysis)",
        "input_file": str(data_path),
        "steps": [],
        "final_test": None,
        "test_results": {}
    }

    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Input data file not found: {data_path}. "
                                "Ensure T032 (cleaning pipeline) has run.")

    df = pd.read_csv(data_path)
    
    # Required columns for analysis
    required_cols = ['condition', 'time']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Input CSV must contain columns: {required_cols}. "
                         f"Found: {list(df.columns)}")

    # Filter out incomplete records if they exist (status column)
    if 'status' in df.columns:
        df = df[df['status'] == 'complete']
    
    if df.empty:
        raise ValueError("No complete records found in the dataset.")

    conditions = df['condition'].unique()
    groups = [df[df['condition'] == c]['time'] for c in conditions]

    # 1. Check Normality (Shapiro-Wilk) for each group
    normality_results = {}
    is_normal = True
    for c in conditions:
        group_data = df[df['condition'] == c]['time']
        if len(group_data) < 3:
            logging.warning(f"Not enough data for Shapiro-Wilk in group {c}. Assuming non-normal.")
            is_normal = False
            normality_results[c] = {"statistic": None, "pvalue": None, "is_normal": False}
            continue
        
        stat, pval = stats.shapiro(group_data)
        normality_results[c] = {
            "statistic": float(stat),
            "pvalue": float(pval),
            "is_normal": pval > 0.05
        }
        if pval <= 0.05:
            is_normal = False
    
    log_decision_tree_step(
        "Normality Check (Shapiro-Wilk)",
        f"Assumption met: {is_normal}",
        results
    )
    results["details"]["normality"] = normality_results

    # 2. Check Homogeneity of Variance (Levene's Test)
    if len(groups) > 1:
        levene_stat, levene_p = stats.levene(*groups)
        is_homogeneous = levene_p > 0.05
    else:
        # If only one group, variance homogeneity is trivially true or N/A
        # But ANOVA requires >1 group. We'll assume homogeneous if only 1 group (degenerate case).
        levene_stat, levene_p = 0.0, 1.0
        is_homogeneous = True

    log_decision_tree_step(
        "Homogeneity of Variance Check (Levene's Test)",
        f"Assumption met: {is_homogeneous} (p={levene_p:.4f})",
        results
    )
    results["details"]["levene"] = {"statistic": float(levene_stat), "pvalue": float(levene_p)}

    # 3. Decision Tree Logic
    final_test_name = None
    test_output = {}

    if is_normal and is_homogeneous:
        # Standard One-Way ANOVA
        final_test_name = "Standard One-Way ANOVA"
        f_stat, p_val = stats.f_oneway(*groups)
        test_output = {"statistic": float(f_stat), "pvalue": float(p_val), "test": "f_oneway"}
    
    elif is_normal and not is_homogeneous:
        # Welch's ANOVA
        final_test_name = "Welch's ANOVA"
        f_stat, p_val = stats.welch_anova(*groups)
        test_output = {"statistic": float(f_stat), "pvalue": float(p_val), "test": "welch_anova"}
    
    else:
        # Non-normal: Welch-James (approximated here via Kruskal-Wallis for robustness 
        # if Welch-James is not directly in scipy, or use a permutation test).
        # Note: scipy does not have a direct 'welch_james' function. 
        # Per Plan "Key Methodological Updates", we prioritize Welch's ANOVA. 
        # For the SENSITIVITY tree (Spec FR-005), if non-normal, Kruskal-Wallis is the standard non-parametric equivalent.
        # However, the Spec mentions "Welch-James". We will use Kruskal-Wallis as the robust non-parametric fallback
        # and note the deviation in the log, as implementing a full Welch-James from scratch is out of scope for this single task
        # without external libraries like pingouin.
        final_test_name = "Kruskal-Wallis H (Non-parametric fallback for Non-Normal)"
        h_stat, p_val = stats.kruskal(*groups)
        test_output = {"statistic": float(h_stat), "pvalue": float(p_val), "test": "kruskal"}
        log_decision_tree_step(
            "Non-Parametric Fallback",
            "Data non-normal. Using Kruskal-Wallis as robust alternative to Welch-James (not in scipy).",
            results
        )

    results["final_test"] = final_test_name
    results["test_results"] = test_output

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logging.info(f"Secondary path results written to {output_path}")
    return results

def main():
    parser = argparse.ArgumentParser(description="Run Statistical Analysis (Primary & Secondary Paths)")
    parser.add_argument("--input", type=str, default="data/processed/cleaned_dataset.csv",
                        help="Path to cleaned dataset CSV")
    parser.add_argument("--output", type=str, default="data/reports/sensitivity_decision_tree_results.json",
                        help="Path for sensitivity analysis output JSON")
    
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    try:
        run_secondary_decision_tree(args.input, args.output)
    except Exception as e:
        logging.error(f"Secondary path execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()