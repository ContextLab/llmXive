"""
Synthetic Dataset Generator for A/B Test Validity Evaluation.

Generates a synthetic corpus of A/B test summaries (both binary and continuous outcomes)
with known ground truth to validate the statistical reconstruction and inconsistency
detection pipeline.

Per FR-030:
- Generates ≥ 10,000 records.
- Includes both binary (z-test/Fisher) and continuous (Welch t-test) outcomes.
- Introduces controlled inconsistencies (p-value drift, effect size drift) to test detection.
- Preserves statistical constraints (e.g., p-values derived from effect sizes and N).
"""

import csv
import json
import logging
import math
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from scipy import stats

# Import from project API surface
from code.src.config import set_rng_seed, SEED
from code.src.models.data_models import ABTestSummary
from code.src.utils.logger import get_default_logger, AuditLogger

# Constants for generation
MIN_RECORDS = 10000
BINARY_RATIO = 0.6  # 60% binary, 40% continuous
INCONSISTENCY_RATE = 0.15  # 15% of records will have intentional inconsistencies
DOMAINS = [
    "tech-news", "health-journal", "marketing-blog", "academic-preprint",
    "e-commerce-report", "finance-bulletin", "social-media-study", "gov-stat"
]
YEARS = list(range(2015, 2025))

logger = get_default_logger(__name__)
audit_logger = AuditLogger(logger)

def _set_seeds(seed: int = SEED) -> None:
    """Ensure deterministic generation."""
    random.seed(seed)
    np.random.seed(seed)
    set_rng_seed(seed)

def _generate_binary_summary(inconsistent: bool = False) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Generates a synthetic binary outcome A/B test summary.
    Returns (summary_dict, ground_truth_dict).
    """
    # Sample sizes
    n_control = random.randint(100, 50000)
    n_treatment = random.randint(100, 50000)

    # Baseline rate and effect size
    p_control = random.uniform(0.05, 0.50)
    effect_size = random.uniform(-0.10, 0.10) # Absolute difference
    p_treatment = p_control + effect_size
    # Clamp probabilities
    p_treatment = max(0.001, min(0.999, p_treatment))

    # Calculate successes
    x_control = int(round(n_control * p_control))
    x_treatment = int(round(n_treatment * p_treatment))

    # Calculate "true" p-value using two-proportion z-test
    # Pooled proportion
    p_pooled = (x_control + x_treatment) / (n_control + n_treatment)
    se = math.sqrt(p_pooled * (1 - p_pooled) * (1/n_control + 1/n_treatment))
    if se == 0:
        se = 1e-9
    z_stat = (p_treatment - p_control) / se
    p_value_true = 2 * (1 - stats.norm.cdf(abs(z_stat)))

    # Introduce inconsistency if requested
    reported_p_value = p_value_true
    reported_effect_size = effect_size

    if inconsistent:
        # Scenario 1: P-value mismatch (report a different p-value)
        if random.random() < 0.5:
            # Shift p-value significantly
            shift = random.uniform(0.02, 0.10) * random.choice([-1, 1])
            reported_p_value = max(0.001, min(0.999, p_value_true + shift))
        # Scenario 2: Effect size mismatch
        else:
            reported_effect_size = effect_size * random.uniform(0.5, 1.5)

    # Construct summary
    summary = {
        "url": f"https://{random.choice(DOMAINS)}.example.com/test/{random.randint(10000, 99999)}",
        "domain": random.choice(DOMAINS),
        "year": random.choice(YEARS),
        "test_type": "binary",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "baseline_rate": round(p_control, 4),
        "treatment_rate": round(p_treatment, 4),
        "reported_p_value": round(reported_p_value, 4),
        "reported_effect_size": round(reported_effect_size, 4),
        "confidence_interval_lower": None,
        "confidence_interval_upper": None,
        "raw_data_available": False
    }

    ground_truth = {
        "true_p_value": round(p_value_true, 6),
        "true_effect_size": round(effect_size, 6),
        "is_inconsistent": inconsistent,
        "inconsistency_type": "p_value_drift" if abs(reported_p_value - p_value_true) > 0.01 else "effect_size_drift"
    }

    return summary, ground_truth

def _generate_continuous_summary(inconsistent: bool = False) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Generates a synthetic continuous outcome A/B test summary.
    Returns (summary_dict, ground_truth_dict).
    """
    # Sample sizes
    n_control = random.randint(20, 5000)
    n_treatment = random.randint(20, 5000)

    # Means and standard deviations
    mu_control = random.uniform(10, 100)
    sigma_control = random.uniform(5, 20)
    effect_size = random.uniform(-10, 10)
    mu_treatment = mu_control + effect_size
    sigma_treatment = sigma_control * random.uniform(0.8, 1.2)

    # Calculate "true" p-value using Welch's t-test
    # Approximation using scipy stats
    # We simulate the t-statistic calculation
    se_diff = math.sqrt((sigma_control**2 / n_control) + (sigma_treatment**2 / n_treatment))
    t_stat = (mu_treatment - mu_control) / se_diff
    # Degrees of freedom (Welch-Satterthwaite equation)
    num = (sigma_control**2 / n_control + sigma_treatment**2 / n_treatment)**2
    den = (sigma_control**2 / n_control)**2 / (n_control - 1) + (sigma_treatment**2 / n_treatment)**2 / (n_treatment - 1)
    df = num / den if den > 0 else 1
    p_value_true = 2 * (1 - stats.t.cdf(abs(t_stat), df))

    # Introduce inconsistency
    reported_p_value = p_value_true
    reported_effect_size = effect_size

    if inconsistent:
        if random.random() < 0.5:
            shift = random.uniform(0.02, 0.10) * random.choice([-1, 1])
            reported_p_value = max(0.001, min(0.999, p_value_true + shift))
        else:
            reported_effect_size = effect_size * random.uniform(0.5, 1.5)

    summary = {
        "url": f"https://{random.choice(DOMAINS)}.example.com/test/{random.randint(10000, 99999)}",
        "domain": random.choice(DOMAINS),
        "year": random.choice(YEARS),
        "test_type": "continuous",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "baseline_rate": round(mu_control, 4), # Reusing 'rate' field for mean in continuous context
        "treatment_rate": round(mu_treatment, 4),
        "reported_p_value": round(reported_p_value, 4),
        "reported_effect_size": round(reported_effect_size, 4),
        "confidence_interval_lower": None,
        "confidence_interval_upper": None,
        "raw_data_available": False,
        "std_control": round(sigma_control, 4),
        "std_treatment": round(sigma_treatment, 4)
    }

    ground_truth = {
        "true_p_value": round(p_value_true, 6),
        "true_effect_size": round(effect_size, 6),
        "is_inconsistent": inconsistent,
        "inconsistency_type": "p_value_drift" if abs(reported_p_value - p_value_true) > 0.01 else "effect_size_drift"
    }

    return summary, ground_truth

def generate_synthetic_dataset(
    output_dir: str,
    num_records: int = MIN_RECORDS,
    seed: int = SEED
) -> Tuple[Path, Path]:
    """
    Generates the synthetic dataset and ground truth files.

    Args:
        output_dir: Directory to write output files.
        num_records: Number of records to generate (default 10,000).
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (path_to_summaries_csv, path_to_ground_truth_json).
    """
    _set_seeds(seed)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    summaries_file = output_path / "synthetic_summaries.csv"
    ground_truth_file = output_path / "synthetic_ground_truth.json"

    logger.info(f"Generating {num_records} synthetic records with seed {seed}...")

    summaries = []
    ground_truths = []

    for i in range(num_records):
        is_inconsistent = random.random() < INCONSISTENCY_RATE
        is_binary = random.random() < BINARY_RATIO

        if is_binary:
            summary, truth = _generate_binary_summary(inconsistent=is_inconsistent)
        else:
            summary, truth = _generate_continuous_summary(inconsistent=is_inconsistent)

        summaries.append(summary)
        ground_truths.append(truth)

        if (i + 1) % 1000 == 0:
            logger.info(f"Generated {i + 1} records...")

    # Write summaries to CSV
    if summaries:
        fieldnames = list(summaries[0].keys())
        with open(summaries_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(summaries)

    # Write ground truth to JSON
    with open(ground_truth_file, 'w', encoding='utf-8') as f:
        json.dump(ground_truths, f, indent=2)

    logger.info(f"Successfully wrote {len(summaries)} summaries to {summaries_file}")
    logger.info(f"Successfully wrote {len(ground_truths)} ground truths to {ground_truth_file}")

    return summaries_file, ground_truth_file

def main():
    """Entry point for synthetic data generation."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate synthetic A/B test dataset")
    parser.add_argument("--output-dir", type=str, default="data/synthetic", help="Output directory")
    parser.add_argument("--num-records", type=int, default=MIN_RECORDS, help="Number of records to generate")
    parser.add_argument("--seed", type=int, default=SEED, help="Random seed")
    args = parser.parse_args()

    try:
        summaries_path, gt_path = generate_synthetic_dataset(
            output_dir=args.output_dir,
            num_records=args.num_records,
            seed=args.seed
        )
        print(f"Synthetic data generation complete.")
        print(f"Summaries: {summaries_path}")
        print(f"Ground Truth: {gt_path}")
    except Exception as e:
        audit_logger.error("ERR-900", f"Failed to generate synthetic dataset: {str(e)}")
        raise

if __name__ == "__main__":
    main()
