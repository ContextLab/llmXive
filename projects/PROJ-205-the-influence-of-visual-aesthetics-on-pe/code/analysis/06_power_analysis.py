import numpy as np
import random

import os
import sys
import json
import argparse
import pandas as pd
from pathlib import Path

# --------------------------------------------------------------------------
# Project Root & Path Helpers
# --------------------------------------------------------------------------

def get_project_root() -> Path:
    """Return the root directory of the project (parent of 'code')."""
    current = Path(__file__).resolve()
    # Navigate up: code/analysis/06_power_analysis.py -> code -> root
    return current.parent.parent.parent

def get_submissions_csv_path() -> Path:
    """Return the path to the raw submissions CSV."""
    return get_project_root() / "data" / "raw" / "submissions.csv"

def get_mock_csv_path() -> Path:
    """Return the path to the mock data CSV for benchmarking."""
    return get_project_root() / "data" / "processed" / "mock_data.csv"

def get_output_path() -> Path:
    """Return the path to the power analysis output JSON."""
    return get_project_root() / "data" / "processed" / "power_analysis.json"

# --------------------------------------------------------------------------
# Data Loading
# --------------------------------------------------------------------------

def load_data_for_power() -> tuple[pd.DataFrame, str]:
    """
    Load real data if available, otherwise raise FileNotFoundError.
    Returns (df, source_string).
    """
    real_path = get_submissions_csv_path()
    mock_path = get_mock_csv_path()

    if real_path.exists() and real_path.stat().st_size > 0:
        df = pd.read_csv(real_path)
        # Filter for complete sessions if the column exists
        if 'submission_status' in df.columns:
            df = df[df['submission_status'] == 'complete']
        if 'session_status' in df.columns:
            df = df[df['session_status'] == 'active']
        return df, "real"

    if mock_path.exists() and mock_path.stat().st_size > 0:
        # Fallback to mock data ONLY if explicitly requested or if no real data exists
        # and we are in a mode where we allow benchmarking.
        # However, per T045, we should fail loudly on missing real data for analysis.
        # The task description says: "If data/raw/submissions.csv exists, use real data.
        # Else, use data/processed/mock_data.csv (from T043a) for benchmarking."
        # We will check for mock data if real is missing, as per task instruction.
        df = pd.read_csv(mock_path)
        return df, "mock"

    raise FileNotFoundError(
        "No data found for power analysis. "
        "Please ensure 'data/raw/submissions.csv' (real data) or "
        "'data/processed/mock_data.csv' (benchmark) exists."
    )

def generate_mock_data_for_power(n: int = 250) -> pd.DataFrame:
    """
    Generate synthetic mock data for power analysis if no real data exists.
    This is a fallback for the 'benchmarking' scenario described in the task.
    """
    np.random.seed(42)
    random.seed(42)

    conditions = ["Professional", "Minimalist", "Low-Quality", "Neutral"]
    participants = [f"mock_{i}" for i in range(n)]

    data = []
    for p_id in participants:
        for cond in conditions:
            # Simulate a small effect for Professional
            mean = 4.0
            if cond == "Professional":
                mean += 0.5
            elif cond == "Low-Quality":
                mean -= 0.3

            rating = int(np.clip(np.random.normal(mean, 1.5), 1, 7))
            data.append({
                "participant_id": p_id,
                "stimulus_id": cond,
                "credibility": rating,
                "professionalism": rating,
                "submission_status": "complete",
                "session_status": "active"
            })

    return pd.DataFrame(data)

# --------------------------------------------------------------------------
# Power Analysis Logic
# --------------------------------------------------------------------------

def estimate_effect_size_from_data(df: pd.DataFrame) -> float:
    """
    Estimate the observed effect size (eta-squared approximation) from the data.
    Uses a simple ANOVA-like calculation on the 'credibility' column across 'stimulus_id'.
    """
    if 'credibility' not in df.columns or 'stimulus_id' not in df.columns:
        return 0.0

    # Calculate group means and overall mean
    group_means = df.groupby('stimulus_id')['credibility'].mean()
    overall_mean = df['credibility'].mean()
    n_total = len(df)
    n_groups = len(group_means)

    # Sum of Squares Between
    ss_between = 0
    for cond, mean in group_means.items():
        n_cond = len(df[df['stimulus_id'] == cond])
        ss_between += n_cond * (mean - overall_mean) ** 2

    # Sum of Squares Total
    ss_total = ((df['credibility'] - overall_mean) ** 2).sum()

    if ss_total == 0:
        return 0.0

    # Eta-squared
    eta_sq = ss_between / ss_total
    return eta_sq

def calculate_power(n: int, effect_size: float, alpha: float = 0.05, k: int = 4) -> float:
    """
    Approximate power for a repeated measures ANOVA using Cohen's f.
    eta_sq = f^2 / (1 + f^2)  =>  f = sqrt(eta_sq / (1 - eta_sq))
    We use a simplified approximation for power based on f and N.
    """
    if effect_size <= 0 or effect_size >= 1:
        return 0.5

    # Convert eta-squared to Cohen's f
    f_sq = effect_size / (1 - effect_size)
    f = np.sqrt(f_sq)

    # Approximate non-centrality parameter lambda
    # lambda = f^2 * N * (k) ? Simplified: lambda = N * f^2
    # For repeated measures, degrees of freedom are adjusted, but for a rough estimate:
    df_num = k - 1
    df_den = (n - 1) * (k - 1)
    lambda_ncp = n * k * f_sq

    # Use scipy to calculate power if available, else return a heuristic
    try:
        from scipy.stats import nc_f
        # Critical F value
        from scipy.stats import f
        f_crit = f.ppf(1 - alpha, df_num, df_den)
        # Power is the probability of F > f_crit under the non-central F distribution
        power = 1 - nc_f.cdf(f_crit, df_num, df_den, lambda_ncp)
        return float(power)
    except ImportError:
        # Heuristic fallback
        # Power ~ 1 - beta. If lambda is high, power is high.
        # This is a very rough approximation.
        return min(1.0, max(0.0, 0.5 + (lambda_ncp / 200)))

def calculate_min_effect_size(n: int, target_power: float = 0.80, alpha: float = 0.05, k: int = 4) -> float:
    """
    Binary search to find the minimum effect size (eta-squared) that yields target_power.
    """
    low = 0.001
    high = 0.5
    tol = 0.001

    while high - low > tol:
        mid = (low + high) / 2
        p = calculate_power(n, mid, alpha, k)
        if p < target_power:
            low = mid
        else:
            high = mid

    return mid

# --------------------------------------------------------------------------
# Main Execution
# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Calculate statistical power for the study.")
    parser.add_argument("--n", type=int, default=250, help="Target sample size for power calculation.")
    parser.add_argument("--alpha", type=float, default=0.05, help="Significance level.")
    parser.add_argument("--power", type=float, default=0.80, help="Target power.")
    args = parser.parse_args()

    # Load data
    try:
        df, source = load_data_for_power()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Estimate observed variance/effect size from the loaded data
    observed_eta_sq = estimate_effect_size_from_data(df)

    # If no real data, and we are in a mode where we generate mock data for benchmarking
    # (The task says: "Else, use data/processed/mock_data.csv (from T043a) for benchmarking")
    # If the file didn't exist, load_data_for_power would have failed.
    # If it exists, we use it. If not, we might need to generate it if the task implies
    # generating it if missing. The task says "use ... from T043a". Assuming T043a ran.
    # If we are in a "no data" scenario and need to generate mock for the calculation itself:
    if source == "mock" and df.empty:
        # Fallback generation if mock file exists but is empty (unlikely but safe)
        df = generate_mock_data_for_power(args.n)
        source = "mock"

    # Calculate min detectable effect size for N=250 (or args.n)
    min_eff = calculate_min_effect_size(args.n, args.power, args.alpha)

    # Calculate actual power for the observed effect size at N=250
    # (Note: observed_eta_sq is from the current sample, we project to N=250)
    # If the current N is different, we use the effect size estimate and plug in N=250
    effective_n = args.n
    current_power = calculate_power(effective_n, observed_eta_sq, args.alpha)

    result = {
        "n": effective_n,
        "alpha": args.alpha,
        "power": current_power,
        "min_effect_size": min_eff,
        "observed_variance": observed_eta_sq,
        "input_source": source
    }

    # Write output
    output_path = get_output_path()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"Power analysis complete. Results written to {output_path}")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()