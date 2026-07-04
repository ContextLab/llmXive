"""
Synthetic Dataset Generator for A/B Test Validity Audit.

Generates a large-scale synthetic dataset of A/B test summaries with known ground truth
to evaluate the statistical consistency detection pipeline.

Produces:
  - data/synthetic/synthetic_validation.csv: The simulated A/B test summaries.
  - data/synthetic/synthetic_ground_truth.json: Metadata and flags for validation.

Constraints:
  - Generates at least 10,000 records.
  - Includes both binary and continuous outcome types.
  - Uses deterministic seeding for reproducibility (Constitution Principle I).
"""

import csv
import json
import logging
import random
import math
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
from scipy import stats

# Import project configuration and logging utilities
from code.src.config import set_rng_seed
from code.src.utils.logger import get_default_logger

# Constants
NUM_RECORDS = 10000
BINARY_RATIO = 0.6  # 60% binary, 40% continuous
RANDOM_SEED = 42
OUTPUT_DIR = Path("data/synthetic")
CSV_OUTPUT = OUTPUT_DIR / "synthetic_validation.csv"
JSON_OUTPUT = OUTPUT_DIR / "synthetic_ground_truth.json"

logger = get_default_logger("synthetic")


def set_all_seeds(seed: int = RANDOM_SEED) -> None:
    """Initialize all random number generators for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"All seeds set to {seed}")


def generate_sample_sizes(min_n: int = 50, max_n: int = 5000) -> Tuple[int, int]:
    """
    Generate realistic sample sizes for control and treatment groups.
    Uses a log-uniform distribution to mimic real-world variance.
    """
    n_control = int(np.random.lognormal(mean=math.log(500), sigma=1.0))
    n_control = max(min_n, min(n_control, max_n))

    # Treatment size varies slightly from control
    ratio = np.random.uniform(0.8, 1.2)
    n_treatment = int(n_control * ratio)
    n_treatment = max(min_n, min(n_treatment, max_n))

    return n_control, n_treatment


def generate_binary_outcome(
    n_control: int,
    n_treatment: int,
    baseline_rate: float,
    effect_size: float,
    is_inconsistent: bool = False
) -> Dict[str, Any]:
    """
    Simulate a binary A/B test outcome.

    Args:
        n_control: Sample size of control group.
        n_treatment: Sample size of treatment group.
        baseline_rate: True conversion rate of control (0.0 - 1.0).
        effect_size: True lift (positive or negative).
        is_inconsistent: If True, report a p-value that contradicts the true effect.

    Returns:
        Dictionary containing simulated metrics and reported statistics.
    """
    # Calculate true rates
    rate_treatment = baseline_rate * (1 + effect_size)
    # Clamp rates to [0, 1]
    rate_treatment = max(0.0, min(1.0, rate_treatment))

    # Simulate successes
    successes_control = np.random.binomial(n_control, baseline_rate)
    successes_treatment = np.random.binomial(n_treatment, rate_treatment)

    observed_rate_control = successes_control / n_control
    observed_rate_treatment = successes_treatment / n_treatment
    observed_effect = (observed_rate_treatment - observed_rate_control) / observed_rate_control if observed_rate_control > 0 else 0.0

    # Calculate true p-value using two-proportion z-test
    # Using pooled proportion for standard error
    p_pooled = (successes_control + successes_treatment) / (n_control + n_treatment)
    se = math.sqrt(p_pooled * (1 - p_pooled) * (1/n_control + 1/n_treatment))
    if se == 0:
        z_stat = 0.0
    else:
        z_stat = (observed_rate_treatment - observed_rate_control) / se

    true_p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))

    # Determine reported p-value
    if is_inconsistent:
        # Flip significance: if true p < 0.05, report > 0.05, and vice versa
        if true_p_value < 0.05:
            reported_p = np.random.uniform(0.06, 0.20)
        else:
            reported_p = np.random.uniform(0.01, 0.049)
    else:
        reported_p = true_p_value

    # Add slight noise to reported p-value to mimic rounding/estimation differences
    noise = np.random.normal(0, 0.001)
    reported_p = max(0.0001, min(0.9999, reported_p + noise))

    return {
        "outcome_type": "binary",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "successes_control": int(successes_control),
        "successes_treatment": int(successes_treatment),
        "baseline_rate": baseline_rate,
        "observed_rate_control": observed_rate_control,
        "observed_rate_treatment": observed_rate_treatment,
        "observed_effect_size": observed_effect,
        "true_p_value": true_p_value,
        "reported_p_value": reported_p,
        "is_inconsistent": is_inconsistent,
        "true_significant": true_p_value < 0.05,
        "reported_significant": reported_p < 0.05
    }


def generate_continuous_outcome(
    n_control: int,
    n_treatment: int,
    baseline_mean: float,
    baseline_std: float,
    effect_size: float,
    is_inconsistent: bool = False
) -> Dict[str, Any]:
    """
    Simulate a continuous A/B test outcome (e.g., revenue per user).

    Args:
        n_control: Sample size of control group.
        n_treatment: Sample size of treatment group.
        baseline_mean: True mean of control.
        baseline_std: True standard deviation of control.
        effect_size: True relative lift.
        is_inconsistent: If True, report a p-value that contradicts the true effect.

    Returns:
        Dictionary containing simulated metrics and reported statistics.
    """
    treatment_mean = baseline_mean * (1 + effect_size)

    # Simulate data (assuming normal distribution for simplicity)
    data_control = np.random.normal(baseline_mean, baseline_std, n_control)
    data_treatment = np.random.normal(treatment_mean, baseline_std, n_treatment)

    obs_mean_control = np.mean(data_control)
    obs_mean_treatment = np.mean(data_treatment)
    obs_std_control = np.std(data_control, ddof=1)
    obs_std_treatment = np.std(data_treatment, ddof=1)

    # Welch's t-test
    # t = (mean1 - mean2) / sqrt(s1^2/n1 + s2^2/n2)
    se_diff = math.sqrt((obs_std_control**2 / n_control) + (obs_std_treatment**2 / n_treatment))
    if se_diff == 0:
        t_stat = 0.0
        df = 0
    else:
        t_stat = (obs_mean_treatment - obs_mean_control) / se_diff
        # Welch-Satterthwaite equation for degrees of freedom
        num = (obs_std_control**2/n_control + obs_std_treatment**2/n_treatment)**2
        den = (obs_std_control**2/n_control)**2/(n_control-1) + (obs_std_treatment**2/n_treatment)**2/(n_treatment-1)
        df = num / den if den > 0 else 0

    true_p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df)) if df > 0 else 1.0

    # Determine reported p-value
    if is_inconsistent:
        if true_p_value < 0.05:
            reported_p = np.random.uniform(0.06, 0.20)
        else:
            reported_p = np.random.uniform(0.01, 0.049)
    else:
        reported_p = true_p_value

    noise = np.random.normal(0, 0.001)
    reported_p = max(0.0001, min(0.9999, reported_p + noise))

    observed_effect = (obs_mean_treatment - obs_mean_control) / obs_mean_control if obs_mean_control > 0 else 0.0

    return {
        "outcome_type": "continuous",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "baseline_mean": baseline_mean,
        "baseline_std": baseline_std,
        "obs_mean_control": obs_mean_control,
        "obs_mean_treatment": obs_mean_treatment,
        "obs_std_control": obs_std_control,
        "obs_std_treatment": obs_std_treatment,
        "observed_effect_size": observed_effect,
        "true_p_value": true_p_value,
        "reported_p_value": reported_p,
        "is_inconsistent": is_inconsistent,
        "true_significant": true_p_value < 0.05,
        "reported_significant": reported_p < 0.05
    }


def generate_synthetic_dataset(
    n_records: int = NUM_RECORDS,
    binary_ratio: float = BINARY_RATIO
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Generate the full synthetic dataset.

    Returns:
        Tuple of (records_list, ground_truth_list).
    """
    records = []
    ground_truth = []

    # Domain list for realism
    domains = ["ecommerce", "saaS", "media", "fintech", "health"]

    for i in range(n_records):
        is_binary = random.random() < binary_ratio
        domain = random.choice(domains)
        year = random.randint(2019, 2024)

        n_c, n_t = generate_sample_sizes()

        # Randomize effect sizes (mostly small, some large)
        # 70% null or tiny effect, 30% meaningful effect
        if random.random() < 0.7:
            true_effect = np.random.uniform(-0.05, 0.05)
        else:
            true_effect = np.random.choice([-0.2, 0.2, -0.1, 0.1, -0.3, 0.3])

        # 10% of records are intentionally inconsistent
        is_inconsistent = random.random() < 0.10

        if is_binary:
            base_rate = np.random.uniform(0.01, 0.20)
            rec = generate_binary_outcome(n_c, n_t, base_rate, true_effect, is_inconsistent)
        else:
            base_mean = np.random.uniform(10.0, 100.0)
            base_std = base_mean * 0.5 # CV = 0.5
            rec = generate_continuous_outcome(n_c, n_t, base_mean, base_std, true_effect, is_inconsistent)

        # Add metadata
        rec["id"] = f"syn_{i:05d}"
        rec["domain"] = domain
        rec["year"] = year
        rec["timestamp"] = datetime.now().isoformat()

        records.append(rec)

        # Ground truth for validation (simplified version)
        gt = {
            "id": rec["id"],
            "outcome_type": rec["outcome_type"],
            "true_significant": rec["true_significant"],
            "reported_significant": rec["reported_significant"],
            "is_inconsistent": rec["is_inconsistent"],
            "true_p_value": rec["true_p_value"],
            "reported_p_value": rec["reported_p_value"],
            "domain": domain,
            "year": year
        }
        ground_truth.append(gt)

    return records, ground_truth


def write_csv_output(records: List[Dict[str, Any]], filepath: Path) -> None:
    """Write records to CSV, flattening nested structures if necessary."""
    if not records:
        logger.warning("No records to write to CSV.")
        return

    # Ensure directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Flatten keys for CSV
    flat_records = []
    for r in records:
        flat = {}
        for k, v in r.items():
            if isinstance(v, (list, dict)):
                flat[k] = json.dumps(v)
            else:
                flat[k] = v
        flat_records.append(flat)

    fieldnames = list(flat_records[0].keys())

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flat_records)

    logger.info(f"Wrote {len(records)} records to {filepath}")


def write_json_output(ground_truth: List[Dict[str, Any]], filepath: Path) -> None:
    """Write ground truth metadata to JSON."""
    if not ground_truth:
        logger.warning("No ground truth to write.")
        return

    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(ground_truth, f, indent=2)

    logger.info(f"Wrote {len(ground_truth)} ground truth entries to {filepath}")


def verify_outcome_types(records: List[Dict[str, Any]]) -> bool:
    """Verify that both binary and continuous outcomes are present."""
    types = set(r["outcome_type"] for r in records)
    has_binary = "binary" in types
    has_continuous = "continuous" in types

    if not (has_binary and has_continuous):
        logger.error(f"Verification failed: Missing outcome types. Found: {types}")
        return False

    logger.info("Verification passed: Both binary and continuous outcomes present.")
    return True


def main() -> None:
    """Main entry point for synthetic data generation."""
    logger.info("Starting synthetic dataset generation...")
    set_all_seeds(RANDOM_SEED)

    try:
        records, ground_truth = generate_synthetic_dataset()

        if not verify_outcome_types(records):
            logger.critical("Failed verification check. Aborting.")
            return

        write_csv_output(records, CSV_OUTPUT)
        write_json_output(ground_truth, JSON_OUTPUT)

        logger.info("Synthetic dataset generation completed successfully.")
    except Exception as e:
        logger.exception(f"Error during generation: {e}")
        raise


if __name__ == "__main__":
    main()
