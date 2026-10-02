"""
Power Analysis Pre-Check Script (T064)

Calculates statistical power based on current sample size (N) and a default
effect size (Cohen's d = 0.5) before running the main ANOVA.

Output: data/processed/power_analysis_report.json
Constraint: If power < 0.80, prints a warning but does not halt execution.
"""

import os
import sys
import json
import argparse
import numpy as np
from pathlib import Path

# Add project root to path for imports
def get_project_root():
    """Returns the project root directory."""
    return Path(__file__).parent.parent.parent

def get_submissions_csv_path():
    """Returns the path to the raw submissions CSV."""
    return get_project_root() / "data" / "raw" / "submissions.csv"

def get_cleaned_csv_path():
    """Returns the path to the cleaned data CSV."""
    return get_project_root() / "data" / "processed" / "clean_data.csv"

def get_output_path():
    """Returns the path for the power analysis report."""
    return get_project_root() / "data" / "processed" / "power_analysis_report.json"

def load_cleaned_data():
    """
    Loads the cleaned data from the processed directory.
    Falls back to raw submissions if cleaned data is not yet available,
    but prioritizes the cleaned file as per pipeline order.
    """
    cleaned_path = get_cleaned_csv_path()
    raw_path = get_submissions_csv_path()

    if cleaned_path.exists():
        import pandas as pd
        return pd.read_csv(cleaned_path)
    elif raw_path.exists():
        import pandas as pd
        return pd.read_csv(raw_path)
    else:
        raise FileNotFoundError(
            f"Data file not found. Expected either {cleaned_path} or {raw_path}. "
            "Please ensure data collection or preprocessing has occurred."
        )

def calculate_power_z_test(mean_diff, sd, n, alpha=0.05, two_tailed=True):
    """
    Approximates power for a test comparing means using a Z-test approximation.
    This is a simplified heuristic for the pre-check.

    Args:
        mean_diff: The expected difference in means (effect size * sd)
        sd: Standard deviation
        n: Sample size per group (assuming balanced for estimation)
        alpha: Significance level
        two_tailed: Whether the test is two-tailed

    Returns:
        Power (probability of rejecting null hypothesis)
    """
    # Standard error of the difference
    se = sd * np.sqrt(2 / n)

    # Z-score under alternative hypothesis
    # delta = (mean_diff - 0) / se
    z_delta = mean_diff / se

    # Critical Z value
    if two_tailed:
        z_crit = np.abs(np.stats.norm.ppf(alpha / 2))
    else:
        z_crit = np.abs(np.stats.norm.ppf(alpha))

    # Power calculation
    # Power = P(Z > z_crit - z_delta) + P(Z < -z_crit - z_delta)
    # Simplified for two-tailed:
    power = np.stats.norm.cdf(z_delta - z_crit) + np.stats.norm.cdf(-z_delta - z_crit)
    return power

def run_power_analysis(df, target_effect_size=0.5, alpha=0.05):
    """
    Runs the power analysis on the provided dataframe.

    Args:
        df: DataFrame containing the data
        target_effect_size: Target Cohen's d (default 0.5)
        alpha: Significance level

    Returns:
        Dictionary with analysis results
    """
    import pandas as pd
    from scipy import stats

    # Determine sample size N
    # We assume the data is in long format with 'participant_id' and 'rating' or similar
    # If the data is already aggregated or in wide format, we adapt.
    # For this pre-check, we count unique participants as N.

    if 'participant_id' in df.columns:
        n_participants = df['participant_id'].nunique()
    elif 'id' in df.columns:
        n_participants = df['id'].nunique()
    else:
        # Fallback: count rows if no ID column (assuming 1 row per participant for simplicity)
        n_participants = len(df)

    # Estimate standard deviation from the data if possible
    # We look for a column that looks like a rating (e.g., 'credibility', 'rating', 'score')
    rating_col = None
    potential_cols = ['credibility', 'rating', 'score', 'value', 'professionalism']
    for col in potential_cols:
        if col in df.columns:
            rating_col = col
            break

    if rating_col and df[rating_col].dtype in ['int64', 'float64']:
        estimated_sd = df[rating_col].std()
        if np.isnan(estimated_sd) or estimated_sd == 0:
            estimated_sd = 1.0 # Fallback to prevent division by zero
    else:
        # If no rating column found, assume a standard deviation of 1.0 (normalized)
        estimated_sd = 1.0

    # Calculate effect size in raw units
    effect_size_raw = target_effect_size * estimated_sd

    # For a repeated measures design, power is generally higher.
    # We use a simplified approximation for the pre-check:
    # Power depends on N, effect size, and alpha.
    # We treat it as a one-sample t-test against a baseline or a paired difference.
    # Standard error for paired difference (assuming correlation ~0.5 for rough estimate)
    # SE_diff = sd * sqrt(2 * (1 - r) / n)
    # We'll use a simplified Z-approximation for speed and robustness in this pre-check.

    # Using statsmodels for a more accurate power analysis if available,
    # otherwise fall back to scipy/numpy approximation.
    try:
        from statsmodels.stats.power import TTestPower
        power_analysis = TTestPower()
        # effect_size = d
        # nobs = N
        # alpha = alpha
        # alternative = 'two-sided'
        calculated_power = power_analysis.solve_power(
            effect_size=target_effect_size,
            nobs1=n_participants,
            alpha=alpha,
            alternative='two-sided'
        )
    except ImportError:
        # Fallback to manual calculation if statsmodels is not available
        # Using the Z-test approximation defined above
        calculated_power = calculate_power_z_test(
            mean_diff=effect_size_raw,
            sd=estimated_sd,
            n=n_participants,
            alpha=alpha,
            two_tailed=True
        )
        # Clamp power to [0, 1]
        calculated_power = max(0.0, min(1.0, calculated_power))

    return {
        "sample_size": int(n_participants),
        "target_effect_size": target_effect_size,
        "estimated_sd": float(estimated_sd),
        "alpha": alpha,
        "calculated_power": float(calculated_power),
        "power_threshold": 0.80,
        "sufficient_power": calculated_power >= 0.80
    }

def main():
    """Main entry point for the power analysis script."""
    parser = argparse.ArgumentParser(description="Run power analysis pre-check.")
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to input data (optional, defaults to cleaned data or raw submissions)."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to output JSON report (optional, defaults to data/processed/power_analysis_report.json)."
    )
    args = parser.parse_args()

    # Determine input path
    if args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        import pandas as pd
        df = pd.read_csv(input_path)
    else:
        df = load_cleaned_data()

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = get_output_path()

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Run analysis
    print(f"Running power analysis on {len(df)} rows...")
    results = run_power_analysis(df)

    # Save results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Power analysis report saved to: {output_path}")
    print(f"Calculated Power: {results['calculated_power']:.4f}")
    print(f"Sufficient Power (>= 0.80): {results['sufficient_power']}")

    if not results['sufficient_power']:
        print("WARNING: Statistical power is below the recommended threshold of 0.80.")
        print("Consider collecting more data before proceeding to the main ANOVA.")
    else:
        print("Power is sufficient for the specified effect size.")

if __name__ == "__main__":
    main()