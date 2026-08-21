"""
Repeated Measures ANOVA analysis script for the Visual Aesthetics Credibility Study.

This script:
1. Loads wide-format data from data/processed/cleaned_data.csv
2. Runs repeated measures ANOVA on credibility ratings across conditions
3. Calculates partial eta-squared effect size
4. If significant, runs Bonferroni-corrected pairwise t-tests with Cohen's d
5. Outputs results to JSON
"""

import os
import sys
import json
import argparse
import random
import numpy as np

# Set seeds for reproducibility
np.random.seed(42)
random.seed(42)

# Add project root to path for imports
def get_project_root():
    """Get the project root directory."""
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current / "data").exists() and (current / "code").exists():
            return current
        current = current.parent
    return Path.cwd()

from pathlib import Path

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

def calculate_partial_eta_squared(ss_effect, ss_error):
    """
    Calculate partial eta-squared effect size.
    
    eta_sq = SS_effect / (SS_effect + SS_error)
    
    Args:
        ss_effect: Sum of squares for the effect
        ss_error: Sum of squares for error
    
    Returns:
        float: Partial eta-squared value
    """
    if ss_effect + ss_error == 0:
        return 0.0
    return ss_effect / (ss_effect + ss_error)

def run_repeated_measures_anova(df):
    """
    Run repeated measures ANOVA on credibility ratings across conditions.
    
    Args:
        df: Wide-format DataFrame with credibility columns
    
    Returns:
        dict: Dictionary with f_stat, df, p_val, eta_sq
    """
    import pandas as pd
    import numpy as np
    from scipy import stats
    
    # Extract credibility columns
    conditions = ["Professional", "Minimalist", "Low-Quality", "Neutral"]
    credibility_cols = [f"credibility_{cond}" for cond in conditions]
    
    # Drop rows with any NaN in credibility columns
    df_clean = df[credibility_cols].dropna()
    
    if len(df_clean) < 2:
        raise ValueError("Not enough data points for ANOVA (need at least 2 participants)")
    
    # Reshape to long format for statsmodels
    df_long = df_clean.melt(var_name="condition", value_name="credibility")
    df_long["participant_id"] = np.repeat(range(len(df_clean)), len(conditions))
    
    # Use statsmodels for repeated measures ANOVA
    from statsmodels.stats.anova import AnovaRM
    
    anova = AnovaRM(df_long, depvar="credibility", subject="participant_id", within=["condition"])
    result = anova.fit()
    
    # Extract F-statistic and p-value
    # The result table has the F-value and p-value for the 'condition' effect
    f_stat = result.fvalues["condition"]
    p_val = result.pvalues["condition"]
    
    # Calculate degrees of freedom
    n_conditions = len(conditions)
    n_participants = len(df_clean)
    
    df_effect = n_conditions - 1
    df_error = (n_participants - 1) * (n_conditions - 1)
    
    # Calculate partial eta-squared
    # We need to compute SS_effect and SS_error manually
    # Using the formula: eta_sq = SS_effect / (SS_effect + SS_error)
    # From F = (SS_effect / df_effect) / (SS_error / df_error)
    # We can derive: SS_effect = F * (df_effect / df_error) * SS_error
    # But we need actual SS values. Let's compute from data.
    
    # Calculate means
    grand_mean = df_long["credibility"].mean()
    
    # SS_total
    ss_total = ((df_long["credibility"] - grand_mean) ** 2).sum()
    
    # SS_subject (participant effect)
    subject_means = df_long.groupby("participant_id")["credibility"].mean()
    ss_subject = ((subject_means - grand_mean) ** 2).sum() * n_conditions
    
    # SS_condition (effect)
    condition_means = df_long.groupby("condition")["credibility"].mean()
    ss_condition = ((condition_means - grand_mean) ** 2).sum() * n_participants
    
    # SS_error = SS_total - SS_subject - SS_condition
    ss_error = ss_total - ss_subject - ss_condition
    
    eta_sq = calculate_partial_eta_squared(ss_condition, ss_error)
    
    return {
        "f_stat": float(f_stat),
        "df": [df_effect, df_error],
        "p_val": float(p_val),
        "eta_sq": float(eta_sq)
    }

def run_conditional_pairwise_tests(df, anova_results):
    """
    Run Bonferroni-corrected pairwise t-tests if ANOVA is significant.
    
    Args:
        df: Wide-format DataFrame
        anova_results: Dictionary with ANOVA results
    
    Returns:
        list: List of pairwise comparison results, or empty list if not significant
    """
    if anova_results["p_val"] >= 0.05:
        return []
    
    import pandas as pd
    import numpy as np
    from scipy import stats
    
    conditions = ["Professional", "Minimalist", "Low-Quality", "Neutral"]
    credibility_cols = [f"credibility_{cond}" for cond in conditions]
    
    df_clean = df[credibility_cols].dropna()
    
    if len(df_clean) < 2:
        return []
    
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
            diff = df_clean[col1] - df_clean[col2]
            pooled_std = diff.std(ddof=1)
            if pooled_std == 0:
                cohens_d = 0.0
            else:
                cohens_d = float(diff.mean() / pooled_std)
            
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
    """Main entry point for ANOVA analysis."""
    parser = argparse.ArgumentParser(description="Run repeated measures ANOVA on credibility ratings")
    parser.add_argument("--input", type=str, required=True, help="Path to wide-format CSV")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON")
    args = parser.parse_args()
    
    print(f"Loading data from {args.input}...")
    df = load_wide_data(args.input)
    
    print("Running repeated measures ANOVA...")
    anova_results = run_repeated_measures_anova(df)
    
    print(f"ANOVA Results: F({anova_results['df'][0]}, {anova_results['df'][1]}) = {anova_results['f_stat']:.4f}, p = {anova_results['p_val']:.4f}, η² = {anova_results['eta_sq']:.4f}")
    
    # Run pairwise tests if significant
    pairwise_results = []
    if anova_results["p_val"] < 0.05:
        print("ANOVA is significant. Running Bonferroni-corrected pairwise t-tests...")
        pairwise_results = run_conditional_pairwise_tests(df, anova_results)
        print(f"Found {len(pairwise_results)} significant pairwise comparisons.")
    
    # Prepare output
    output = {
        "f_stat": anova_results["f_stat"],
        "df": anova_results["df"],
        "n": len(df),
        "p_val": anova_results["p_val"],
        "eta_sq": anova_results["eta_sq"],
        "bonferroni_factor": len(pairwise_results) + 6 if pairwise_results else 6,  # 6 comparisons total
        "pairwise": pairwise_results
    }
    
    # Write output
    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"Results written to {args.output}")

if __name__ == "__main__":
    main()
