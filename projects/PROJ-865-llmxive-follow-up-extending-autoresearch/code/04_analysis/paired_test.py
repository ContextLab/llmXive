"""
T029h: Paired t-test/Wilcoxon with Effect Size

Performs Paired t-test and Wilcoxon signed-rank test on "Time-to-Pivot" differences
from data/derived/results.csv. Handles censored data (TIMEOUT_SECONDS) by including
them as the maximum observed value in the Wilcoxon test to avoid survivorship bias.

Output: data/derived/time_diff_paired_results.json
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.stats.effect_size import EffectSize

# Import local config for TIMEOUT_SECONDS
# We assume the script runs from project root or code/04_analysis/
# Adjust path resolution to find utils/config.py
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.config import TIMEOUT_SECONDS
from utils.logging import get_logger, log_stage_start, log_stage_end

logger = get_logger(__name__)

INPUT_FILE = Path("data/derived/results.csv")
OUTPUT_FILE = Path("data/derived/time_diff_paired_results.json")

def load_results_csv() -> pd.DataFrame:
    """Load and validate the results CSV."""
    if not INPUT_FILE.exists():
        logger.error(f"Input file not found: {INPUT_FILE}")
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE)
    required_cols = ["task_id", "method", "time_to_pivot", "success"]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {INPUT_FILE}: {missing_cols}")

    logger.info(f"Loaded {len(df)} rows from {INPUT_FILE}")
    return df

def extract_paired_differences(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract paired time-to-pivot values for Rule Engine and Baseline.
    Returns (rule_times, baseline_times) aligned by task_id.
    """
    # Pivot to wide format: task_id as index, methods as columns
    pivot_df = df.pivot_table(
        index="task_id",
        columns="method",
        values="time_to_pivot",
        aggfunc="first"  # Assuming unique task_id per method
    )

    if "Rule Engine" not in pivot_df.columns or "Baseline" not in pivot_df.columns:
        available = pivot_df.columns.tolist()
        raise ValueError(f"Expected 'Rule Engine' and 'Baseline' methods. Found: {available}")

    rule_times = pivot_df["Rule Engine"].to_numpy()
    baseline_times = pivot_df["Baseline"].to_numpy()

    # Handle missing values (e.g., if one method failed to produce a time)
    # For this test, we only consider pairs where BOTH have values.
    # Censored values (TIMEOUT_SECONDS) are valid values and should be kept.
    mask = ~(np.isnan(rule_times) | np.isnan(baseline_times))
    rule_times = rule_times[mask]
    baseline_times = baseline_times[mask]

    if len(rule_times) == 0:
        raise ValueError("No paired data available after filtering NaNs.")

    logger.info(f"Extracted {len(rule_times)} paired observations.")
    return rule_times, baseline_times

def calculate_cohens_d_paired(x: np.ndarray, y: np.ndarray) -> float:
    """
    Calculate Cohen's d for paired samples.
    d = mean(x - y) / std(x - y)
    """
    diffs = x - y
    mean_diff = np.mean(diffs)
    std_diff = np.std(diffs, ddof=1)  # Sample std dev

    if std_diff == 0:
        return 0.0

    return mean_diff / std_diff

def calculate_confidence_interval(diffs: np.ndarray, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate 95% CI for the mean difference.
    """
    n = len(diffs)
    mean_diff = np.mean(diffs)
    std_err = np.std(diffs, ddof=1) / np.sqrt(n)
    t_crit = stats.t.ppf((1 + confidence) / 2.0, n - 1)
    ci_lower = mean_diff - t_crit * std_err
    ci_upper = mean_diff + t_crit * std_err
    return ci_lower, ci_upper

def run_paired_tests(rule_times: np.ndarray, baseline_times: np.ndarray) -> Dict[str, Any]:
    """
    Perform Paired t-test and Wilcoxon signed-rank test.
    Include censored data (TIMEOUT_SECONDS) in Wilcoxon.
    """
    diffs = rule_times - baseline_times

    # 1. Normality Test (Shapiro-Wilk)
    stat_shapiro, p_shapiro = stats.shapiro(diffs)
    logger.info(f"Shapiro-Wilk Test: statistic={stat_shapiro:.4f}, p-value={p_shapiro:.4f}")

    test_type = "Paired t-test"
    p_value = None
    statistic = None

    if p_shapiro > 0.05:
        # Normal distribution assumed -> Paired t-test
        logger.info("Data appears normal. Running Paired t-test.")
        statistic, p_value = stats.ttest_rel(rule_times, baseline_times)
    else:
        # Non-normal -> Wilcoxon signed-rank test
        # Include censored values (they are just numbers equal to TIMEOUT_SECONDS)
        logger.info("Data not normal. Running Wilcoxon signed-rank test.")
        statistic, p_value = stats.wilcoxon(rule_times, baseline_times)
        test_type = "Wilcoxon signed-rank test"

    # 2. Effect Size (Cohen's d)
    cohen_d = calculate_cohens_d_paired(rule_times, baseline_times)
    logger.info(f"Cohen's d: {cohen_d:.4f}")

    # 3. Confidence Interval for mean difference
    ci_lower, ci_upper = calculate_confidence_interval(diffs)
    logger.info(f"95% CI for mean difference: [{ci_lower:.4f}, {ci_upper:.4f}]")

    return {
        "p_value": float(p_value),
        "statistic": float(statistic),
        "test_type": test_type,
        "cohen_d": float(cohen_d),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "normality_p_value": float(p_shapiro),
        "sample_size": int(len(diffs))
    }

def main():
    log_stage_start("T029h", "Paired Test with Effect Size")

    try:
        # Load Data
        df = load_results_csv()

        # Extract Paired Differences
        rule_times, baseline_times = extract_paired_differences(df)

        # Run Tests
        results = run_paired_tests(rule_times, baseline_times)

        # Ensure Output Directory Exists
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Write Output
        with open(OUTPUT_FILE, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"Results written to {OUTPUT_FILE}")
        print(f"Success: {OUTPUT_FILE} created.")

    except Exception as e:
        logger.error(f"Execution failed: {e}")
        # Re-raise to ensure the script exits with non-zero code on failure
        raise

    finally:
        log_stage_end("T029h")

if __name__ == "__main__":
    main()