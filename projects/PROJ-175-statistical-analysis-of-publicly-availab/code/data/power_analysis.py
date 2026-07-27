"""
Power Analysis Module (T008).

Computes unified sample size N_unified based on variance from pilot data (T013b).
Outputs data/power_analysis.json and data/split_config.json.
"""
import os
import sys
import json
import math
from pathlib import Path

# Add parent directory to path to allow imports if run as script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.memory_monitor import check_memory_limit

# Constants
PILOT_STATS_PATH = Path("data/raw/pilot_stats.json")
POWER_OUTPUT_PATH = Path("data/power_analysis.json")
SPLIT_CONFIG_OUTPUT_PATH = Path("data/split_config.json")

# Target parameters
TARGET_EFFECT_SIZE = 0.1
TARGET_POWER = 0.8
ALPHA = 0.05

def load_pilot_stats() -> dict:
    """
    Load variance estimates from the pilot data statistics file.
    Raises FileNotFoundError if the file is missing (fail loudly).
    """
    if not PILOT_STATS_PATH.exists():
        raise FileNotFoundError(
            f"Pilot statistics not found at {PILOT_STATS_PATH}. "
            "Ensure T013b (Pilot Data Fetch) has been executed."
        )
    
    with open(PILOT_STATS_PATH, 'r') as f:
        return json.load(f)

def calculate_sample_size(variance: float, effect_size: float, power: float, alpha: float) -> int:
    """
    Calculate the required sample size N for a two-sample t-test approximation.
    
    Formula: N = 2 * ( (Z_alpha + Z_beta)^2 * sigma^2 ) / delta^2
    Where:
      - Z_alpha is the critical value for significance level alpha (two-tailed)
      - Z_beta is the critical value for power (1 - beta)
      - sigma^2 is the variance
      - delta is the effect size (difference in means)
    
    Args:
        variance (float): Estimated variance from pilot data.
        effect_size (float): Minimum detectable effect size (delta).
        power (float): Desired statistical power (1 - beta).
        alpha (float): Significance level.
    
    Returns:
        int: Required sample size per group (rounded up).
    """
    # Check memory limit before heavy calculation (though this is light)
    check_memory_limit(limit_mb=6144)

    if variance <= 0:
        raise ValueError("Variance must be positive to calculate sample size.")
    
    if effect_size <= 0:
        raise ValueError("Effect size must be positive.")

    # Calculate Z-scores
    # For two-tailed alpha, we use alpha/2
    z_alpha = abs(math.erfcinv(alpha) * math.sqrt(2)) 
    # For power, we use beta = 1 - power
    z_beta = abs(math.erfcinv(2 * (1 - power)) * math.sqrt(2))

    # Standard normal inverse approximation using erfcinv (since scipy is available but erfcinv is math-safe)
    # Note: math.erfcinv is available in Python 3.8+. 
    # If strictly needed without scipy, we can use a simple approximation or import from scipy.stats if available.
    # Given T002 includes scipy, let's use scipy for precision if available, otherwise fallback to math.
    try:
        from scipy.stats import norm
        z_alpha = norm.ppf(1 - alpha/2)
        z_beta = norm.ppf(power)
    except ImportError:
        # Fallback approximation if scipy is somehow missing (should not happen per T002)
        # Approximation for Z
        def approx_ppf(p):
            # Rational approximation for normal quantile
            if p <= 0: return -10
            if p >= 1: return 10
            t = math.sqrt(-2 * math.log(min(p, 1-p)))
            c0, c1, c2, d1, d2, d3 = 2.515517, 0.802853, 0.010328, 1.432788, 0.189269, 0.001308
            return t - (c0 + c1*t + c2*t**2) / (1 + d1*t + d2*t**2 + d3*t**3)
        
        z_alpha = approx_ppf(1 - alpha/2)
        z_beta = approx_ppf(power)

    # Calculate N per group
    # N = 2 * ( (Z_alpha + Z_beta)^2 * sigma^2 ) / delta^2
    numerator = 2 * ((z_alpha + z_beta) ** 2) * variance
    denominator = effect_size ** 2
    
    n_per_group = math.ceil(numerator / denominator)
    
    # Total unified sample size (N_unified)
    n_unified = n_per_group * 2
    
    return n_unified

def main():
    """
    Main entry point for T008.
    1. Loads pilot stats.
    2. Calculates N_unified.
    3. Writes data/power_analysis.json and data/split_config.json.
    """
    print("Starting Power Analysis (T008)...")
    
    # 1. Load Pilot Data
    try:
        pilot_stats = load_pilot_stats()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Extract variance. The pilot stats should contain 'variance' or 'mean_variance'.
    # Assuming T013b produced a structure like {"variance": float, ...}
    if "variance" not in pilot_stats:
        # Fallback if structure is different, e.g., {'mean_variance': ...}
        if "mean_variance" in pilot_stats:
            variance = pilot_stats["mean_variance"]
        else:
            raise KeyError(
                f"Pilot stats file {PILOT_STATS_PATH} missing 'variance' or 'mean_variance' key. "
                f"Keys found: {list(pilot_stats.keys())}"
            )
    else:
        variance = pilot_stats["variance"]

    print(f"Loaded variance from pilot: {variance}")

    # 2. Calculate Sample Size
    try:
        n_unified = calculate_sample_size(
            variance=variance,
            effect_size=TARGET_EFFECT_SIZE,
            power=TARGET_POWER,
            alpha=ALPHA
        )
    except Exception as e:
        print(f"ERROR calculating sample size: {e}")
        sys.exit(1)

    print(f"Calculated unified sample size N_unified: {n_unified}")

    # 3. Prepare Output Data
    power_analysis_result = {
        "N_unified": n_unified,
        "effect_size": TARGET_EFFECT_SIZE,
        "power": TARGET_POWER,
        "alpha": ALPHA,
        "pilot_variance": variance,
        "method": "Two-sample t-test approximation (Z-score)",
        "timestamp": __import__('datetime').datetime.now().isoformat()
    }

    split_config_result = {
        "N_unified": n_unified,
        "train_ratio": 0.8,
        "test_ratio": 0.2,
        "estimated_train_size": int(n_unified * 0.8),
        "estimated_test_size": int(n_unified * 0.2),
        "seed": 42, # From T005
        "status": "pending_split", # Will be updated by T019
        "timestamp": __import__('datetime').datetime.now().isoformat()
    }

    # 4. Write Artifacts
    # Ensure output directories exist
    POWER_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SPLIT_CONFIG_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(POWER_OUTPUT_PATH, 'w') as f:
        json.dump(power_analysis_result, f, indent=2)
    print(f"Wrote power analysis to {POWER_OUTPUT_PATH}")

    with open(SPLIT_CONFIG_OUTPUT_PATH, 'w') as f:
        json.dump(split_config_result, f, indent=2)
    print(f"Wrote split config to {SPLIT_CONFIG_OUTPUT_PATH}")

    print("T008 Power Analysis completed successfully.")

if __name__ == "__main__":
    main()
