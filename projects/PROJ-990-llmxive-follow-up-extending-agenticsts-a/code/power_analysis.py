"""
Task T044: Power Analysis

Performs a power analysis to determine the statistical power of the experiment
given the sample size, effect size, and significance level.

Parameters:
- alpha: 0.05
- target_power: 0.8
- effect_size: 0.2 (Cohen's d)

It reads the sample size from the existing data splits (train/validation/test)
or the config_state.json if available, and calculates the achieved power.
It writes the results to data/processed/power_analysis.json.

If the sample size is small (n < 300), it includes a warning as per T053 requirements.
"""
import os
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
ALPHA = 0.05
TARGET_POWER = 0.8
EFFECT_SIZE = 0.2
OUTPUT_PATH = Path("data/processed/power_analysis.json")
CONFIG_STATE_PATH = Path("data/processed/config_state.json")
TRAIN_SET_PATH = Path("data/processed/train_set.csv")
TEST_SET_PATH = Path("data/processed/test_set.csv")

def load_sample_size() -> int:
    """
    Determine the sample size (n) from the available data splits.
    Priority:
    1. Check if train_set.csv exists and count rows.
    2. Check if test_set.csv exists and count rows.
    3. Check config_state.json for sample size info.
    4. Default to a small number if nothing is found (should not happen if pipeline ran).
    """
    n = 0

    if TRAIN_SET_PATH.exists():
        try:
            df = pd.read_csv(TRAIN_SET_PATH)
            n = len(df)
            logger.info(f"Sample size found in train_set.csv: {n}")
        except Exception as e:
            logger.warning(f"Could not read train_set.csv: {e}")

    if n == 0 and TEST_SET_PATH.exists():
        try:
            df = pd.read_csv(TEST_SET_PATH)
            n = len(df)
            logger.info(f"Sample size found in test_set.csv: {n}")
        except Exception as e:
            logger.warning(f"Could not read test_set.csv: {e}")

    if n == 0 and CONFIG_STATE_PATH.exists():
        try:
            with open(CONFIG_STATE_PATH, 'r') as f:
                config = json.load(f)
                if 'sample_size' in config:
                    n = config['sample_size']
                    logger.info(f"Sample size found in config_state.json: {n}")
        except Exception as e:
            logger.warning(f"Could not read config_state.json: {e}")

    if n == 0:
        logger.warning("No sample size found in data splits or config. Defaulting to 100 for calculation.")
        n = 100

    return n

def calculate_power(n: int, effect_size: float, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Calculate the statistical power for a two-sample t-test (or paired t-test approximation).
    Uses the non-central t-distribution.

    Returns a dictionary with:
    - sample_size: n
    - effect_size: d
    - alpha: significance level
    - achieved_power: calculated power
    - target_power: 0.8
    - is_power_adequate: boolean
    - warning: string if n < 300
    """
    # For a two-tailed t-test, we approximate power using the non-centrality parameter
    # ncp = d * sqrt(n / 2) for two independent groups of size n/2 each.
    # However, the task implies a paired test (McNemar/t-test on pairs).
    # For paired t-test with n pairs: ncp = d * sqrt(n).
    # We will assume a paired design as per the pipeline context (Dynamic vs Static on same trajectories).

    ncp = effect_size * np.sqrt(n)
    df = n - 1

    # Critical t-value for two-tailed test
    t_crit = stats.t.ppf(1 - alpha / 2, df)

    # Power is the probability that the t-statistic exceeds t_crit under the alternative hypothesis
    # Power = 1 - CDF(t_crit) + CDF(-t_crit)
    # Using the non-central t-distribution
    power = 1 - stats.nct.cdf(t_crit, df, ncp) + stats.nct.cdf(-t_crit, df, ncp)

    return {
        "sample_size": n,
        "effect_size": effect_size,
        "alpha": alpha,
        "achieved_power": float(power),
        "target_power": TARGET_POWER,
        "is_power_adequate": power >= TARGET_POWER,
        "warning": None
    }

def main():
    logger.info("Starting Power Analysis (T044).")

    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Load sample size
    n = load_sample_size()
    logger.info(f"Using sample size n={n}.")

    # Calculate power
    result = calculate_power(n, EFFECT_SIZE, ALPHA)

    # Add warning if sample size is marginal (per T053 requirements)
    if n < 300:
        warning_msg = "Statistical power marginal (n<300); results should be interpreted with caution."
        result["warning"] = warning_msg
        logger.warning(warning_msg)

    # Write output
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Power analysis complete. Results written to {OUTPUT_PATH}")
    logger.info(f"Achieved power: {result['achieved_power']:.4f} (Target: {TARGET_POWER})")

    return result

if __name__ == "__main__":
    main()
