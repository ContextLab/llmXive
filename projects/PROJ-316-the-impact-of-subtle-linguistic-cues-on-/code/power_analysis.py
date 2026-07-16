"""
Power Analysis for the Impact of Subtle Linguistic Cues on Perceived Authenticity.

This script calculates the required sample size (N) to achieve a statistical power
of >= 0.80 for a multiple linear regression model, based on assumed effect sizes (f²)
derived from literature on linguistic cues and perceived authenticity.

It outputs the results to data/results/power_analysis_results.yaml.
"""
import os
import math
import yaml
from pathlib import Path

# Ensure output directory exists
output_dir = Path("data/results")
output_dir.mkdir(parents=True, exist_ok=True)

# Constants
TARGET_POWER = 0.80
ALPHA = 0.05
# Assumed effect sizes (f²) based on typical small-to-medium effects in social science linguistics
# Cohen's guidelines: small=0.02, medium=0.15, large=0.35
# We assume a small-to-medium effect for subtle cues: 0.05
ASSUMED_F2 = 0.05
# Number of predictors in the model (Linguistic features + Controls)
# Predictors: first_person_count, hedge_count, hedge_ratio, sentiment_score (4)
# Controls: conversation_length, turn_count (2)
# Total predictors (u) = 6
NUM_PREDICTORS = 6

def calculate_noncentrality_parameter(f2, u, n):
    """
    Calculates the noncentrality parameter (lambda) for the F-test.
    lambda = f² * (u + v + 1) approx f² * N for large N, but strictly:
    lambda = f² * (u + 1) * (N - u - 1) ?
    Actually, standard definition: lambda = f² * (u + v + 1) is not quite right for sample size iteration.
    Standard: lambda = f² * (u + v + 1) where v = N - u - 1.
    So lambda = f² * (u + N - u - 1 + 1) = f² * N.
    Wait, let's use the standard approximation for power calculation:
    Power = 1 - beta = P(F > F_crit | lambda)
    lambda = f² * (u + v + 1) is incorrect.
    Correct: lambda = f² * (u + v + 1) is for the numerator?
    Let's stick to the standard formula: lambda = f² * (u + v + 1) is often used in G*Power context
    where u = numerator df, v = denominator df.
    Actually, for regression:
    u = k (number of predictors)
    v = N - k - 1
    lambda = f² * (u + v + 1) = f² * (k + N - k - 1 + 1) = f² * N.
    This is the standard approximation.
    """
    return ASSUMED_F2 * (NUM_PREDICTORS + 1) # Wait, lambda = f^2 * N is the approximation for large N?
    # Let's use the precise definition: lambda = f^2 * (u + v + 1)
    # where u = predictors, v = error df.
    # But v depends on N. So lambda = f^2 * N.
    # Let's re-verify: G*Power uses lambda = f^2 * (u + v + 1) = f^2 * N.
    # So lambda = f^2 * N.
    return ASSUMED_F2 * n

def calculate_critical_f(u, v, alpha):
    """
    Approximates the critical F value using the inverse F distribution.
    Since we don't want to depend on scipy.stats if not available, we use a standard approximation
    or import scipy if available. Given the requirements.txt includes scipy, we use it.
    """
    try:
        from scipy.stats import f
        return f.ppf(1 - alpha, u, v)
    except ImportError:
        # Fallback approximation if scipy is missing (unlikely given requirements)
        # F_crit approx 1 + z_alpha * sqrt(2/u) ... rough
        return 3.0 # Placeholder, will fail if scipy missing

def calculate_power(u, v, lambda_val, alpha):
    """
    Calculates power given degrees of freedom and noncentrality parameter.
    Uses scipy.stats.ncf (non-central F).
    """
    try:
        from scipy.stats import ncf
        f_crit = calculate_critical_f(u, v, alpha)
        # Power = P(F > F_crit | df1, df2, lambda)
        # ncf.cdf gives P(F <= x). So power = 1 - cdf.
        power = 1 - ncf.cdf(f_crit, u, v, lambda_val)
        return power
    except ImportError:
        raise ImportError("scipy is required for power analysis calculations.")

def find_required_sample_size(u, target_power, alpha, f2):
    """
    Iteratively finds the minimum N such that Power >= target_power.
    """
    n = u + 10 # Start with a reasonable minimum
    max_iterations = 10000
    found = False

    for _ in range(max_iterations):
        v = n - u - 1
        if v <= 0:
            n += 1
            continue

        lambda_val = f2 * n
        power = calculate_power(u, v, lambda_val, alpha)

        if power >= target_power:
            return n, power
        
        n += 1

    return None, 0.0

def main():
    print(f"Running Power Analysis for Regression Model...")
    print(f"  Effect Size (f²): {ASSUMED_F2}")
    print(f"  Number of Predictors (u): {NUM_PREDICTORS}")
    print(f"  Target Power: {TARGET_POWER}")
    print(f"  Alpha: {ALPHA}")

    required_n, achieved_power = find_required_sample_size(
        u=NUM_PREDICTORS,
        target_power=TARGET_POWER,
        alpha=ALPHA,
        f2=ASSUMED_F2
    )

    if required_n is None:
        result = {
            "status": "failed",
            "reason": "Could not achieve target power within iteration limit.",
            "assumed_effect_size_f2": ASSUMED_F2,
            "num_predictors": NUM_PREDICTORS
        }
    else:
        # Check against a hypothetical budget (e.g., 1000 samples)
        BUDGET = 1000
        status = "underpowered" if required_n > BUDGET else "sufficient"
        
        result = {
            "status": status,
            "required_sample_size_N": required_n,
            "achieved_power_at_N": round(achieved_power, 4),
            "assumed_effect_size_f2": ASSUMED_F2,
            "num_predictors": NUM_PREDICTORS,
            "alpha": ALPHA,
            "target_power": TARGET_POWER,
            "budget_N": BUDGET,
            "note": "Sample size calculated for multiple linear regression with specified predictors."
        }

    output_path = output_dir / "power_analysis_results.yaml"
    with open(output_path, "w") as f:
        yaml.dump(result, f, default_flow_style=False, sort_keys=False)

    print(f"Results written to: {output_path}")
    print(f"Required N: {required_n}")
    if required_n > BUDGET:
        print(f"WARNING: Required N ({required_n}) exceeds budget ({BUDGET}). Project may be underpowered.")
    else:
        print(f"OK: Required N ({required_n}) is within budget ({BUDGET}).")

if __name__ == "__main__":
    main()
