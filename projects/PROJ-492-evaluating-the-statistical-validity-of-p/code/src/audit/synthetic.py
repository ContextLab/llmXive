"""
Synthetic dataset generator for A/B test validity evaluation (FR-030).

Generates a synthetic corpus of A/B test summaries with known ground truth
to evaluate the inconsistency detection pipeline.

Produces:
  - data/synthetic/summary_synthetic.csv: The synthetic summaries (>= 10,000 records)
  - data/synthetic/ground_truth_synthetic.csv: The ground truth labels for validation
"""
import csv
import json
import logging
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
from scipy import stats

from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger

# Constants
MIN_RECORDS = 10000
TARGET_RECORDS = 10500
DOMAINS = ["tech", "finance", "health", "e-commerce", "education"]
OUTCOME_TYPES = ["binary", "continuous"]

logger = get_default_logger(__name__)

def set_all_seeds(seed: int = SEED) -> None:
    """Set random seeds for reproducibility."""
    set_rng_seed(seed)
    np.random.seed(seed)
    logger.info(f"Random seeds set to {seed}")

def generate_sample_sizes(n_total: int = TARGET_RECORDS) -> List[Tuple[int, int]]:
    """
    Generate realistic sample sizes for control and treatment groups.
    Sizes vary between 100 and 50,000 to simulate real-world variance.
    """
    sizes = []
    for _ in range(n_total):
        # Log-normal distribution for realistic size variance
        base_size = np.random.lognormal(mean=6.0, sigma=1.0)
        n_control = int(np.clip(base_size, 100, 50000))
        # Treatment size is usually similar but can vary slightly
        ratio = np.random.uniform(0.8, 1.2)
        n_treatment = int(np.clip(n_control * ratio, 100, 50000))
        sizes.append((n_control, n_treatment))
    return sizes

def _generate_binary_outcome_data(
    n_control: int,
    n_treatment: int,
    baseline_rate: float,
    effect_size: float,
    is_inconsistent: bool,
    rng: np.random.Generator
) -> Dict[str, Any]:
    """
    Generate binary outcome data (conversion rates).
    Returns observed rates and the "true" p-value vs reported p-value.
    """
    # True effect
    true_effect = effect_size if not is_inconsistent else effect_size * 1.5
    control_rate = baseline_rate
    treatment_rate = baseline_rate + true_effect
    treatment_rate = np.clip(treatment_rate, 0.01, 0.99)

    # Generate observed counts
    x_control = rng.binomial(n_control, control_rate)
    x_treatment = rng.binomial(n_treatment, treatment_rate)

    observed_control_rate = x_control / n_control
    observed_treatment_rate = x_treatment / n_treatment
    observed_effect = observed_treatment_rate - observed_control_rate

    # Calculate true p-value (two-proportion z-test)
    p_pool = (x_control + x_treatment) / (n_control + n_treatment)
    se = math.sqrt(p_pool * (1 - p_pool) * (1/n_control + 1/n_treatment))
    if se == 0:
        z_stat = 0.0
    else:
        z_stat = (observed_treatment_rate - observed_control_rate) / se
    true_p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))

    # Generate reported p-value (potentially inconsistent)
    if is_inconsistent:
        # Inconsistency: report a p-value that doesn't match the data
        # e.g., report p < 0.05 when true p > 0.05, or vice versa
        if true_p_value < 0.05:
            reported_p = rng.uniform(0.06, 0.20)
        else:
            reported_p = rng.uniform(0.01, 0.04)
    else:
        # Add small noise to true p-value
        reported_p = true_p_value * rng.uniform(0.95, 1.05)
        reported_p = np.clip(reported_p, 0.001, 0.999)

    return {
        "n_control": n_control,
        "n_treatment": n_treatment,
        "x_control": x_control,
        "x_treatment": x_treatment,
        "observed_control_rate": observed_control_rate,
        "observed_treatment_rate": observed_treatment_rate,
        "observed_effect": observed_effect,
        "true_p_value": true_p_value,
        "reported_p_value": reported_p,
        "is_inconsistent": is_inconsistent,
        "outcome_type": "binary"
    }

def _generate_continuous_outcome_data(
    n_control: int,
    n_treatment: int,
    baseline_mean: float,
    effect_size: float,
    is_inconsistent: bool,
    rng: np.random.Generator
) -> Dict[str, Any]:
    """
    Generate continuous outcome data (e.g., time on site, revenue).
    """
    # True effect
    true_effect = effect_size if not is_inconsistent else effect_size * 1.5
    control_mean = baseline_mean
    treatment_mean = baseline_mean + true_effect

    # Assume standard deviation is roughly 20% of the mean
    std_dev = baseline_mean * 0.2
    if std_dev < 1.0: std_dev = 1.0

    # Generate samples
    samples_control = rng.normal(control_mean, std_dev, n_control)
    samples_treatment = rng.normal(treatment_mean, std_dev, n_treatment)

    obs_mean_control = np.mean(samples_control)
    obs_mean_treatment = np.mean(samples_treatment)
    obs_effect = obs_mean_treatment - obs_mean_control

    # Welch's t-test
    t_stat, true_p_value = stats.ttest_ind(
        samples_control, samples_treatment, equal_var=False
    )

    # Generate reported p-value
    if is_inconsistent:
        if true_p_value < 0.05:
            reported_p = rng.uniform(0.06, 0.20)
        else:
            reported_p = rng.uniform(0.01, 0.04)
    else:
        reported_p = true_p_value * rng.uniform(0.95, 1.05)
        reported_p = np.clip(reported_p, 0.001, 0.999)

    return {
        "n_control": n_control,
        "n_treatment": n_treatment,
        "observed_mean_control": obs_mean_control,
        "observed_mean_treatment": obs_mean_treatment,
        "observed_effect": obs_effect,
        "observed_std_control": np.std(samples_control, ddof=1),
        "observed_std_treatment": np.std(samples_treatment, ddof=1),
        "true_p_value": true_p_value,
        "reported_p_value": reported_p,
        "is_inconsistent": is_inconsistent,
        "outcome_type": "continuous"
    }

def generate_synthetic_dataset(
    n_records: int = TARGET_RECORDS,
    inconsistency_rate: float = 0.15
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Generate the full synthetic dataset.
    Returns (summaries, ground_truth).
    """
    set_all_seeds()
    rng = np.random.default_rng(SEED)

    summaries = []
    ground_truth = []

    sample_sizes = generate_sample_sizes(n_records)

    logger.info(f"Generating {n_records} synthetic records...")

    for i in range(n_records):
        n_control, n_treatment = sample_sizes[i]
        is_binary = rng.choice([True, False])
        is_inconsistent = rng.random() < inconsistency_rate
        domain = rng.choice(DOMAINS)

        if is_binary:
            baseline = rng.uniform(0.05, 0.30)
            effect = rng.choice([-0.02, 0.02]) * rng.uniform(0.5, 2.0)
            data = _generate_binary_outcome_data(
                n_control, n_treatment, baseline, effect, is_inconsistent, rng
            )
            summary_row = {
                "id": f"syn_{i:05d}",
                "domain": domain,
                "outcome_type": "binary",
                "n_control": data["n_control"],
                "n_treatment": data["n_treatment"],
                "control_rate": round(data["observed_control_rate"], 4),
                "treatment_rate": round(data["observed_treatment_rate"], 4),
                "effect_size": round(data["observed_effect"], 4),
                "reported_p_value": round(data["reported_p_value"], 4),
                "test_type": "z-test" if (n_control + n_treatment) > 30 else "fisher",
                "year": rng.choice([2022, 2023, 2024, 2025])
            }
        else:
            baseline = rng.uniform(10.0, 100.0)
            effect = rng.choice([-5.0, 5.0]) * rng.uniform(0.5, 2.0)
            data = _generate_continuous_outcome_data(
                n_control, n_treatment, baseline, effect, is_inconsistent, rng
            )
            summary_row = {
                "id": f"syn_{i:05d}",
                "domain": domain,
                "outcome_type": "continuous",
                "n_control": data["n_control"],
                "n_treatment": data["n_treatment"],
                "control_mean": round(data["observed_mean_control"], 2),
                "treatment_mean": round(data["observed_mean_treatment"], 2),
                "effect_size": round(data["observed_effect"], 2),
                "reported_p_value": round(data["reported_p_value"], 4),
                "test_type": "welch-t",
                "year": rng.choice([2022, 2023, 2024, 2025])
            }

        summaries.append(summary_row)

        ground_truth_row = {
            "id": summary_row["id"],
            "domain": domain,
            "outcome_type": summary_row["outcome_type"],
            "true_p_value": round(data["true_p_value"], 6),
            "reported_p_value": round(data["reported_p_value"], 4),
            "is_inconsistent": is_inconsistent,
            "p_difference": round(abs(data["true_p_value"] - data["reported_p_value"]), 6),
            "sample_size_mismatch": False # We generate consistent sample sizes here
        }
        ground_truth.append(ground_truth_row)

        if (i + 1) % 1000 == 0:
            logger.info(f"Generated {i + 1} records...")

    return summaries, ground_truth

def write_summaries_to_csv(data: List[Dict[str, Any]], path: Path) -> None:
    """Write synthetic summaries to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(data[0].keys())
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    logger.info(f"Wrote {len(data)} records to {path}")

def verify_outcome_types(data: List[Dict[str, Any]]) -> bool:
    """Verify that both binary and continuous outcomes exist."""
    types = set(row["outcome_type"] for row in data)
    if "binary" in types and "continuous" in types:
        logger.info("Verification passed: Both binary and continuous outcomes present.")
        return True
    else:
        logger.error(f"Verification failed: Missing outcome types. Found: {types}")
        return False

def main() -> None:
    """Main entry point for synthetic data generation."""
    output_dir = Path("code/data/synthetic")
    summary_path = output_dir / "summary_synthetic.csv"
    ground_truth_path = output_dir / "ground_truth_synthetic.csv"

    logger.info("Starting synthetic dataset generation...")

    summaries, ground_truth = generate_synthetic_dataset()

    # Verify constraints
    if len(summaries) < MIN_RECORDS:
        raise ValueError(f"Generated {len(summaries)} records, less than required {MIN_RECORDS}")

    if not verify_outcome_types(summaries):
        raise ValueError("Outcome type verification failed")

    write_summaries_to_csv(summaries, summary_path)
    write_summaries_to_csv(ground_truth, ground_truth_path)

    logger.info("Synthetic dataset generation completed successfully.")

if __name__ == "__main__":
    main()
