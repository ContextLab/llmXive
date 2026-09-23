"""
Power Analysis Script for PROJ-205
Calculates minimum detectable effect size and observed power for N=250
using real data from the cleaned dataset.
"""
import os
import sys
import json
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.stats.power import FTestAnovaPower

# Add project root to path for imports if running as script
def get_project_root():
    """Get the root directory of the project."""
    return Path(__file__).resolve().parent.parent.parent

def get_submissions_csv_path():
    """Get path to raw submissions CSV."""
    return get_project_root() / "data" / "raw" / "submissions.csv"

def get_cleaned_csv_path():
    """Get path to processed cleaned CSV."""
    return get_project_root() / "data" / "processed" / "cleaned_data.csv"

def get_output_path():
    """Get path for power analysis results."""
    return get_project_root() / "data" / "processed" / "power_analysis_results.json"

def load_cleaned_data(input_path=None):
    """
    Load the cleaned wide-format data.
    Expects columns: participant_id, condition_Professional_credibility, etc.
    """
    if input_path is None:
        input_path = get_cleaned_csv_path()

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Cleaned data not found at {input_path}. "
                                "Run code/analysis/00_preprocess.py first.")

    df = pd.read_csv(input_path)
    return df

def estimate_effect_size_from_data(df):
    """
    Estimate the observed effect size (eta squared) from the cleaned data.
    Uses a simple ANOVA on the 'credibility' metric across conditions.
    """
    # Identify credibility columns for each condition
    # Assuming wide format: columns contain 'credibility'
    cred_cols = [c for c in df.columns if 'credibility' in c.lower()]

    if len(cred_cols) < 2:
        raise ValueError("Could not find sufficient credibility columns in wide data.")

    # Reshape to long format for statsmodels
    # We need: value, condition (factor)
    # The column names usually look like: condition_Professional_credibility
    # We need to extract the condition name.
    # Assumption: The condition name is the part before '_credibility' or '_professionalism'
    # Let's parse the column name to get the condition.
    # Format expected from preprocess: condition_<NAME>_credibility

    long_data = []
    for col in cred_cols:
        # Extract condition name. Example: "condition_Professional_credibility" -> "Professional"
        parts = col.split('_')
        # Heuristic: The condition is the second part if first is 'condition', or last-1 if ends with credibility
        if parts[0] == 'condition':
            condition_name = parts[1]
        else:
            # Fallback: try to find the part that isn't 'credibility'
            condition_name = parts[0].replace('condition_', '')

        values = df[col].dropna()
        for v in values:
            long_data.append({'condition': condition_name, 'value': v})

    long_df = pd.DataFrame(long_data)

    if long_df.empty:
        raise ValueError("No data points found for effect size calculation.")

    # Calculate Sum of Squares for One-Way ANOVA manually to get Eta Squared
    # Eta Squared = SS_between / SS_total
    grand_mean = long_df['value'].mean()
    ss_total = ((long_df['value'] - grand_mean) ** 2).sum()

    ss_between = 0
    for cond, group in long_df.groupby('condition'):
        n = len(group)
        cond_mean = group['value'].mean()
        ss_between += n * ((cond_mean - grand_mean) ** 2)

    if ss_total == 0:
        eta_sq = 0.0
    else:
        eta_sq = ss_between / ss_total

    return eta_sq, len(df)

def calculate_min_detectable_effect_size(n=250, k=4, alpha=0.05, power=0.80):
    """
    Calculate the minimum detectable effect size (f) for a given sample size.
    k = number of groups (conditions)
    """
    # Degrees of freedom
    df_num = k - 1
    df_denom = n - k

    # Use statsmodels to solve for effect size f
    analysis = FTestAnovaPower()
    try:
        effect_size_f = analysis.solve_power(
            nobs=n,
            alpha=alpha,
            power=power,
            k_groups=k,
            effect_size=None
        )
    except Exception:
        # Fallback if solver fails: use a standard small effect size
        effect_size_f = 0.15

    return effect_size_f

def calculate_power_for_observed_effect(effect_size_f, n, k=4, alpha=0.05):
    """
    Calculate the statistical power given an observed effect size.
    """
    analysis = FTestAnovaPower()
    try:
        power = analysis.solve_power(
            effect_size=effect_size_f,
            nobs=n,
            alpha=alpha,
            k_groups=k,
            power=None
        )
    except Exception:
        power = 0.0

    return power

def main():
    parser = argparse.ArgumentParser(description="Calculate power analysis metrics.")
    parser.add_argument('--input', type=str, default=None,
                        help="Path to cleaned data CSV (default: data/processed/cleaned_data.csv)")
    parser.add_argument('--output', type=str, default=None,
                        help="Path to output JSON (default: data/processed/power_analysis_results.json)")
    parser.add_argument('--sample-size', type=int, default=250,
                        help="Target sample size for power calculation")
    args = parser.parse_args()

    # Resolve paths
    input_path = args.input if args.input else get_cleaned_csv_path()
    output_path = args.output if args.output else get_output_path()

    print(f"Loading cleaned data from: {input_path}")
    try:
        df = load_cleaned_data(input_path)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print(f"Data loaded. Rows: {len(df)}")

    # 1. Estimate observed effect size from the real data
    print("Estimating observed effect size (Eta Squared) from data...")
    try:
        observed_eta_sq, actual_n = estimate_effect_size_from_data(df)
    except ValueError as e:
        print(f"ERROR calculating effect size: {e}")
        sys.exit(1)

    print(f"Observed Eta Squared: {observed_eta_sq:.4f} (N={actual_n})")

    # Convert Eta Squared to Cohen's f for statsmodels
    # f = sqrt(eta_sq / (1 - eta_sq))
    if observed_eta_sq >= 1.0:
        f_obs = 10.0 # Cap at high value
    else:
        f_obs = np.sqrt(observed_eta_sq / (1 - observed_eta_sq))

    # 2. Calculate minimum detectable effect size for N=250
    k_conditions = 4 # Professional, Minimalist, Low-Quality, Neutral
    min_detectable_f = calculate_min_detectable_effect_size(
        n=args.sample_size, k=k_conditions
    )

    # 3. Calculate power for the observed effect size at N=250
    observed_power = calculate_power_for_observed_effect(
        f_obs, n=args.sample_size, k=k_conditions
    )

    # 4. Compile results
    results = {
        "sample_size": args.sample_size,
        "actual_data_rows": actual_n,
        "effect_size": {
            "type": "Cohen's f (derived from Eta Squared)",
            "observed_f": float(f_obs),
            "observed_eta_squared": float(observed_eta_sq),
            "min_detectable_f": float(min_detectable_f)
        },
        "power": {
            "alpha": 0.05,
            "observed_power_at_N250": float(observed_power),
            "target_power": 0.80
        },
        "analysis_method": "One-way ANOVA power analysis (F-test)",
        "notes": "Effect size derived from cleaned data. Power calculated for N=250."
    }

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Power analysis complete. Results saved to: {output_path}")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
