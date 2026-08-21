"""
Pairwise t-tests with effect sizes for the Visual Aesthetics Credibility Study.

This script:
1. Loads wide-format data
2. Runs paired t-tests for all condition pairs
3. Applies Bonferroni correction
4. Calculates Cohen's d effect sizes
5. Outputs results to JSON
"""

import os
import sys
import json
import random
import argparse
import numpy as np

# Set seeds for reproducibility
np.random.seed(42)
random.seed(42)

from pathlib import Path

def get_project_root():
    """Get the project root directory."""
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current / "data").exists() and (current / "code").exists():
            return current
        current = current.parent
    return Path.cwd()

PROJECT_ROOT = get_project_root()
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

def load_wide_data(input_path):
    """
    Load wide-format data from CSV.
    
    Args:
        input_path: Path to the wide-format CSV file
    
    Returns:
        pandas DataFrame with wide-format data
    """
    import pandas as pd
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Verify required columns exist
    required_cols = [
        "credibility_Professional",
        "credibility_Minimalist",
        "credibility_Low-Quality",
        "credibility_Neutral"
    ]
    
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    return df

def calculate_cohens_d(group1, group2, paired=True):
    """
    Calculate Cohen's d effect size.
    
    For paired samples: d = mean(diff) / std(diff)
    For independent samples: d = (mean1 - mean2) / pooled_std
    
    Args:
        group1: First group of values
        group2: Second group of values
        paired: Whether samples are paired (default: True)
    
    Returns:
        float: Cohen's d value
    """
    import numpy as np
    
    if paired:
        diff = group1 - group2
        std_diff = diff.std(ddof=1)
        if std_diff == 0:
            return 0.0
        return float(diff.mean() / std_diff)
    else:
        mean1, mean2 = group1.mean(), group2.mean()
        std1, std2 = group1.std(ddof=1), group2.std(ddof=1)
        n1, n2 = len(group1), len(group2)
        
        # Pooled standard deviation
        pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
        
        if pooled_std == 0:
            return 0.0
        
        return float((mean1 - mean2) / pooled_std)

def run_pairwise_tests_with_effects(df):
    """
    Run all pairwise t-tests with Bonferroni correction and Cohen's d.
    
    Args:
        df: Wide-format DataFrame with credibility columns
    
    Returns:
        list: List of dictionaries with comparison results
    """
    import pandas as pd
    import numpy as np
    from scipy import stats
    
    conditions = ["Professional", "Minimalist", "Low-Quality", "Neutral"]
    credibility_cols = [f"credibility_{cond}" for cond in conditions]
    
    df_clean = df[credibility_cols].dropna()
    
    if len(df_clean) < 2:
        raise ValueError("Not enough data points for pairwise tests (need at least 2 participants)")
    
    # All pairwise comparisons
    comparisons = []
    n_comparisons = len(conditions) * (len(conditions) - 1) // 2
    bonferroni_factor = n_comparisons
    
    for i in range(len(conditions)):
        for j in range(i + 1, len(conditions)):
            cond1 = conditions[i]
            cond2 = conditions[j]
            col1 = f"credibility_{cond1}"
            col2 = f"credibility_{cond2}"
            
            # Paired t-test
            t_stat, p_raw = stats.ttest_rel(df_clean[col1], df_clean[col2])
            
            # Bonferroni correction
            p_adj = min(p_raw * bonferroni_factor, 1.0)
            
            # Cohen's d for paired samples
            cohens_d = calculate_cohens_d(df_clean[col1], df_clean[col2], paired=True)
            
            comparisons.append({
                "comparison": f"{cond1} vs {cond2}",
                "p_val": float(p_adj),
                "raw_p_val": float(p_raw),
                "bonferroni_factor": bonferroni_factor,
                "cohens_d": cohens_d,
                "df_pairwise": len(df_clean) - 1
            })
    
    return comparisons

def main():
    """Main entry point for pairwise analysis."""
    parser = argparse.ArgumentParser(description='Run pairwise t-tests with effect sizes')
    parser.add_argument("--input", type=str, required=True, help="Path to wide-format CSV")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON")
    args = parser.parse_args()
    
    print(f"Loading data from {args.input}...")
    df = load_wide_data(args.input)
    
    print("Running pairwise t-tests with Bonferroni correction...")
    pairwise_results = run_pairwise_tests_with_effects(df)
    
    print(f"Found {len(pairwise_results)} pairwise comparisons.")
    
    # Prepare output
    output = {
        "n": len(df),
        "bonferroni_factor": len(pairwise_results),
        "pairwise": pairwise_results
    }
    
    # Write output
    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"Results written to {args.output}")

if __name__ == "__main__":
    main()
