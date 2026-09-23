"""
Synthetic Dataset Generator for A/B Test Validity Audit.

Generates a large-scale synthetic dataset of A/B test summaries (both binary
and continuous outcomes) to serve as ground truth for evaluating the
statistical consistency of public reports.

This module adheres to FR-030 and generates datasets with >= 10,000 records
that preserve statistical constraints (e.g., p-values derived from sample
sizes and effect sizes).
"""
import csv
import json
import logging
import math
import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

import numpy as np
from scipy import stats

from code.src.config import SEED, set_rng_seed
from code.src.models.data_models import ABTestSummary
from code.src.utils.logger import get_default_logger

# Constants for synthetic generation
MIN_RECORDS = 10000
BINARY_RATIO = 0.6  # 60% binary, 40% continuous
DOMAIN_LIST = [
    "techcrunch.com", "medium.com", "optimizely.com", "unbounce.com",
    "vwo.com", "google-analytics.com", "shopify.com", "stripe.com",
    "mailchimp.com", "hubspot.com"
]
OUTCOME_TYPES = ["conversion_rate", "click_through_rate", "revenue_per_user", "time_on_site", "bounce_rate"]

logger = get_default_logger(__name__)

def _set_seed():
    """Ensure deterministic generation."""
    set_rng_seed(SEED)

def _generate_binary_outcome(
    n_control: int,
    n_treatment: int,
    p_control: float,
    lift: float,
    noise_level: float = 0.0
) -> Tuple[float, float, float, float]:
    """
    Generate synthetic binary A/B test metrics.

    Args:
        n_control: Sample size for control group.
        n_treatment: Sample size for treatment group.
        p_control: Baseline conversion rate.
        lift: Expected lift (e.g., 0.10 for 10% increase).
        noise_level: Amount of noise to add to p-value (0.0 = perfect calculation).

    Returns:
        Tuple of (p_control_observed, p_treatment_observed, p_value, effect_size).
    """
    p_treatment = p_control * (1 + lift)
    p_treatment = min(p_treatment, 0.99)  # Cap at 99%

    # Generate counts (simulate binomial draws)
    # To ensure statistical consistency for the "truth", we calculate the expected
    # values, then add a tiny bit of binomial noise if requested, but for the
    # purpose of a "ground truth" generator that the reconstructor should match,
    # we often want the reported stats to be mathematically consistent with the
    # reported counts.
    # However, to make it realistic, we generate counts from the distribution.
    count_control = np.random.binomial(n_control, p_control)
    count_treatment = np.random.binomial(n_treatment, p_treatment)

    # Observed rates
    p_hat_control = count_control / n_control
    p_hat_treatment = count_treatment / n_treatment

    # Calculate pooled p for Z-test
    p_pooled = (count_control + count_treatment) / (n_control + n_treatment)

    # Standard error
    se = math.sqrt(p_pooled * (1 - p_pooled) * (1/n_control + 1/n_treatment))
    if se == 0:
        se = 1e-9

    # Z-statistic
    z_stat = (p_hat_treatment - p_hat_control) / se

    # Two-tailed p-value
    p_val = 2 * (1 - stats.norm.cdf(abs(z_stat)))

    # Add noise if requested (simulating reporting error or slight deviation)
    if noise_level > 0:
        p_val = max(0.0, min(1.0, p_val + np.random.uniform(-noise_level, noise_level)))

    effect_size = p_hat_treatment - p_hat_control

    return p_hat_control, p_hat_treatment, p_val, effect_size

def _generate_continuous_outcome(
    n_control: int,
    n_treatment: int,
    mu_control: float,
    sigma_control: float,
    lift: float,
    ratio_sigma: float = 1.0
) -> Tuple[float, float, float, float, float]:
    """
    Generate synthetic continuous A/B test metrics (Welch's t-test scenario).

    Returns:
        Tuple of (mean_control, mean_treatment, p_value, effect_size, std_control, std_treatment)
    """
    mu_treatment = mu_control * (1 + lift)
    sigma_treatment = sigma_control * ratio_sigma

    # Generate samples
    sample_control = np.random.normal(mu_control, sigma_control, n_control)
    sample_treatment = np.random.normal(mu_treatment, sigma_treatment, n_treatment)

    mean_control = float(np.mean(sample_control))
    mean_treatment = float(np.mean(sample_treatment))
    std_control = float(np.std(sample_control, ddof=1))
    std_treatment = float(np.std(sample_treatment, ddof=1))

    # Welch's t-test
    t_stat, p_val = stats.ttest_ind(
        sample_control, sample_treatment, equal_var=False
    )

    effect_size = mean_treatment - mean_control

    return mean_control, mean_treatment, p_val, effect_size, std_control, std_treatment

def _generate_synthetic_record(
    record_id: int,
    outcome_type: str
) -> Dict[str, Any]:
    """
    Generate a single synthetic A/B test summary record.
    """
    _set_seed() # Ensure reproducibility per record if needed, though global seed is set

    # Randomize sample sizes (realistic range)
    n_control = random.randint(500, 50000)
    n_treatment = random.randint(500, 50000)

    # Randomize domain and year
    domain = random.choice(DOMAIN_LIST)
    year = random.randint(2018, 2025)

    # Determine outcome specifics
    if outcome_type == "binary":
        # Binary parameters
        p_control = random.uniform(0.05, 0.50)
        # Lift: mostly small positive, some negative, some zero
        lift = random.choice([
            random.uniform(0.01, 0.20),  # Positive lift
            random.uniform(-0.15, -0.01), # Negative lift
            0.0                           # No effect
        ])
        
        # Occasional noise to simulate reporting inconsistencies
        noise = random.uniform(0, 0.05) if random.random() < 0.1 else 0.0

        p_c, p_t, p_val, eff = _generate_binary_outcome(
            n_control, n_treatment, p_control, lift, noise
        )

        return {
            "id": record_id,
            "url": f"https://{domain}/ab-test-{record_id}",
            "domain": domain,
            "year": year,
            "outcome_type": "binary",
            "metric_name": "conversion_rate" if random.random() > 0.5 else "click_through_rate",
            "n_control": n_control,
            "n_treatment": n_treatment,
            "baseline_rate": p_c,
            "treatment_rate": p_t,
            "p_value": p_val,
            "effect_size": eff,
            "is_significant": p_val < 0.05,
            "test_type": "z-test" if min(n_control, n_treatment) > 30 else "fisher",
            "confidence_interval": f"[{eff - 1.96 * abs(eff * 0.1):.4f}, {eff + 1.96 * abs(eff * 0.1):.4f}]"
        }

    else:
        # Continuous parameters
        mu = random.uniform(10.0, 100.0)
        sigma = mu * 0.2  # 20% CV
        lift = random.choice([
            random.uniform(0.05, 0.30),
            random.uniform(-0.25, -0.05),
            0.0
        ])
        ratio_sigma = random.uniform(0.8, 1.2)

        m_c, m_t, p_val, eff, s_c, s_t = _generate_continuous_outcome(
            n_control, n_treatment, mu, sigma, lift, ratio_sigma
        )

        return {
            "id": record_id,
            "url": f"https://{domain}/ab-test-{record_id}",
            "domain": domain,
            "year": year,
            "outcome_type": "continuous",
            "metric_name": random.choice(["revenue_per_user", "time_on_site", "bounce_rate"]),
            "n_control": n_control,
            "n_treatment": n_treatment,
            "baseline_rate": m_c,
            "treatment_rate": m_t,
            "p_value": p_val,
            "effect_size": eff,
            "is_significant": p_val < 0.05,
            "test_type": "welch-t",
            "std_control": s_c,
            "std_treatment": s_t,
            "confidence_interval": f"[{eff - 1.96 * abs(eff * 0.1):.4f}, {eff + 1.96 * abs(eff * 0.1):.4f}]"
        }

def generate_synthetic_dataset(
    output_dir: Path,
    count: int = MIN_RECORDS,
    binary_ratio: float = BINARY_RATIO
) -> Tuple[Path, Path]:
    """
    Generate the full synthetic dataset and ground truth file.

    Args:
        output_dir: Directory to write output files.
        count: Total number of records to generate.
        binary_ratio: Fraction of records that are binary outcomes.

    Returns:
        Tuple of (path_to_summaries_csv, path_to_ground_truth_json).
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    summaries_path = output_dir / "synthetic_summaries.csv"
    ground_truth_path = output_dir / "synthetic_ground_truth.json"

    logger.info(f"Generating {count} synthetic records to {output_dir}")

    records = []
    ground_truth = {
        "generated_at": datetime.now().isoformat(),
        "seed": SEED,
        "total_records": count,
        "binary_count": 0,
        "continuous_count": 0,
        "records": []
    }

    binary_count = int(count * binary_ratio)
    continuous_count = count - binary_count

    for i in range(count):
        is_binary = i < binary_count
        outcome_type = "binary" if is_binary else "continuous"
        
        record = _generate_synthetic_record(i, outcome_type)
        records.append(record)
        
        if is_binary:
            ground_truth["binary_count"] += 1
        else:
            ground_truth["continuous_count"] += 1

        # Store ground truth details (including internal params if needed, 
        # but for now the record itself is the ground truth for the audit)
        ground_truth["records"].append(record)

    # Write CSV summaries (for the pipeline to ingest)
    if records:
        fieldnames = list(records[0].keys())
        with open(summaries_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)

    # Write JSON ground truth
    with open(ground_truth_path, 'w', encoding='utf-8') as f:
        json.dump(ground_truth, f, indent=2)

    logger.info(f"Successfully generated {count} records. "
                f"Binary: {ground_truth['binary_count']}, Continuous: {ground_truth['continuous_count']}")
    logger.info(f"Output files: {summaries_path}, {ground_truth_path}")

    return summaries_path, ground_truth_path

def main():
    """Entry point for synthetic dataset generation."""
    output_dir = Path("data/synthetic")
    count = 10500  # Slightly above 10k to ensure >= 10000 requirement

    try:
        summaries_path, ground_truth_path = generate_synthetic_dataset(output_dir, count)
        print(f"Synthetic dataset generated successfully.")
        print(f"Summaries: {summaries_path}")
        print(f"Ground Truth: {ground_truth_path}")
    except Exception as e:
        logger.error(f"Failed to generate synthetic dataset: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
