"""
Synthetic dataset generator for A/B test audit validation (FR-030).

Generates at least 10,000 simulated A/B test summaries with both binary
and continuous outcomes to validate the inconsistency detection pipeline.
"""
import csv
import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
from scipy import stats

from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.models.data_models import ABTestSummary

logger = get_default_logger(__name__)


def set_all_seeds(seed: int = SEED) -> None:
    """Set seeds for all random number generators for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Seeds set to {seed} for reproducibility")


def generate_sample_sizes(n_total: int = 10000) -> List[Tuple[int, int]]:
    """
    Generate realistic sample sizes for A and B groups.

    Returns a list of (n_a, n_b) tuples.
    Sample sizes are drawn from a log-normal distribution to mimic real-world variance.
    """
    # Log-normal parameters chosen to produce sample sizes between ~50 and ~10000
    mu, sigma = np.log(500), 0.8
    n_a = np.random.lognormal(mu, sigma, n_total).astype(int)
    n_b = np.random.lognormal(mu, sigma, n_total).astype(int)

    # Ensure minimum sample sizes
    n_a = np.maximum(n_a, 50)
    n_b = np.maximum(n_b, 50)

    return list(zip(n_a, n_b))


def generate_binary_outcome(
    n_a: int,
    n_b: int,
    baseline_rate: float,
    effect_size: float,
    introduce_inconsistency: bool = False,
    inconsistency_severity: float = 0.1
) -> Dict[str, Any]:
    """
    Generate a binary outcome A/B test summary.

    Args:
        n_a: Sample size for group A
        n_b: Sample size for group B
        baseline_rate: Conversion rate for group A (0-1)
        effect_size: True effect size (difference in proportions)
        introduce_inconsistency: If True, intentionally report inconsistent p-values
        inconsistency_severity: Magnitude of p-value distortion if inconsistent

    Returns:
        Dictionary with n_a, n_b, x_a, x_b, p_value, effect_size_reported, outcome_type
    """
    # True rates
    p_a = baseline_rate
    p_b = baseline_rate + effect_size

    # Ensure rates stay in valid range
    p_a = np.clip(p_a, 0.01, 0.99)
    p_b = np.clip(p_b, 0.01, 0.99)

    # Generate observed successes (binomial)
    x_a = np.random.binomial(n_a, p_a)
    x_b = np.random.binomial(n_b, p_b)

    # Calculate observed proportions
    prop_a = x_a / n_a
    prop_b = x_b / n_b
    observed_effect = prop_b - prop_a

    # Calculate true p-value using two-proportion z-test
    # Pooled proportion for null hypothesis
    pooled_p = (x_a + x_b) / (n_a + n_b)
    se = np.sqrt(pooled_p * (1 - pooled_p) * (1/n_a + 1/n_b))
    if se > 0:
        z_stat = observed_effect / se
        true_p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    else:
        true_p_value = 1.0

    # Decide whether to report inconsistent p-value
    if introduce_inconsistency and random.random() < 0.3:  # 30% of inconsistent cases
        # Distort the p-value
        distortion_factor = 1 + random.uniform(-inconsistency_severity, inconsistency_severity)
        reported_p_value = np.clip(true_p_value * distortion_factor, 0.001, 0.999)
    else:
        reported_p_value = true_p_value

    return {
        "n_a": int(n_a),
        "n_b": int(n_b),
        "x_a": int(x_a),
        "x_b": int(x_b),
        "p_value": float(reported_p_value),
        "effect_size_reported": float(observed_effect),
        "outcome_type": "binary",
        "true_p_value": float(true_p_value),
        "true_effect": float(observed_effect),
        "is_inconsistent": introduce_inconsistency and random.random() < 0.3
    }


def generate_continuous_outcome(
    n_a: int,
    n_b: int,
    baseline_mean: float,
    baseline_std: float,
    effect_size: float,
    introduce_inconsistency: bool = False,
    inconsistency_severity: float = 0.1
) -> Dict[str, Any]:
    """
    Generate a continuous outcome A/B test summary.

    Args:
        n_a: Sample size for group A
        n_b: Sample size for group B
        baseline_mean: Mean for group A
        baseline_std: Standard deviation for group A
        effect_size: True difference in means
        introduce_inconsistency: If True, intentionally report inconsistent p-values
        inconsistency_severity: Magnitude of p-value distortion if inconsistent

    Returns:
        Dictionary with n_a, n_b, mean_a, mean_b, std_a, std_b, p_value, effect_size_reported, outcome_type
    """
    # True parameters
    mean_a = baseline_mean
    mean_b = baseline_mean + effect_size
    std_a = baseline_std
    std_b = baseline_std * np.random.uniform(0.8, 1.2)  # Slight variation in std

    # Generate samples
    sample_a = np.random.normal(mean_a, std_a, n_a)
    sample_b = np.random.normal(mean_b, std_b, n_b)

    # Observed statistics
    obs_mean_a = np.mean(sample_a)
    obs_mean_b = np.mean(sample_b)
    obs_std_a = np.std(sample_a, ddof=1)
    obs_std_b = np.std(sample_b, ddof=1)
    observed_effect = obs_mean_b - obs_mean_a

    # Welch's t-test for true p-value
    if obs_std_a > 0 and obs_std_b > 0:
        se_diff = np.sqrt((obs_std_a**2 / n_a) + (obs_std_b**2 / n_b))
        t_stat = observed_effect / se_diff if se_diff > 0 else 0
        # Welch-Satterthwaite degrees of freedom
        df_num = (obs_std_a**2 / n_a + obs_std_b**2 / n_b)**2
        df_den = ((obs_std_a**2 / n_a)**2 / (n_a - 1)) + ((obs_std_b**2 / n_b)**2 / (n_b - 1))
        df = df_num / df_den if df_den > 0 else min(n_a, n_b) - 1
        true_p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df))
    else:
        true_p_value = 1.0

    # Decide whether to report inconsistent p-value
    if introduce_inconsistency and random.random() < 0.3:
        distortion_factor = 1 + random.uniform(-inconsistency_severity, inconsistency_severity)
        reported_p_value = np.clip(true_p_value * distortion_factor, 0.001, 0.999)
    else:
        reported_p_value = true_p_value

    return {
        "n_a": int(n_a),
        "n_b": int(n_b),
        "mean_a": float(obs_mean_a),
        "mean_b": float(obs_mean_b),
        "std_a": float(obs_std_a),
        "std_b": float(obs_std_b),
        "p_value": float(reported_p_value),
        "effect_size_reported": float(observed_effect),
        "outcome_type": "continuous",
        "true_p_value": float(true_p_value),
        "true_effect": float(observed_effect),
        "is_inconsistent": introduce_inconsistency and random.random() < 0.3
    }


def generate_synthetic_dataset(
    n_total: int = 10000,
    binary_ratio: float = 0.5,
    output_dir: Path = Path("data/synthetic"),
    seed: int = SEED
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Generate a synthetic dataset of A/B test summaries.

    Args:
        n_total: Total number of summaries to generate
        binary_ratio: Proportion of binary outcomes (0-1)
        output_dir: Directory to write output files
        seed: Random seed for reproducibility

    Returns:
        Tuple of (list of summaries, counts by outcome type)
    """
    set_all_seeds(seed)
    output_dir.mkdir(parents=True, exist_ok=True)

    n_binary = int(n_total * binary_ratio)
    n_continuous = n_total - n_binary

    summaries = []
    counts = {"binary": 0, "continuous": 0}

    # Generate sample sizes
    sample_sizes = generate_sample_sizes(n_total)

    for i in range(n_total):
        n_a, n_b = sample_sizes[i]
        is_binary = i < n_binary

        if is_binary:
            # Binary outcome parameters
            baseline_rate = np.random.uniform(0.05, 0.5)
            # Effect size: small to medium (0 to 0.15 absolute difference)
            effect_size = np.random.choice([-1, 1]) * np.random.uniform(0, 0.15)
            introduce_inconsistency = np.random.random() < 0.25  # 25% inconsistent

            summary = generate_binary_outcome(
                n_a, n_b, baseline_rate, effect_size, introduce_inconsistency
            )
            counts["binary"] += 1
        else:
            # Continuous outcome parameters
            baseline_mean = np.random.uniform(10, 100)
            baseline_std = np.random.uniform(5, 20)
            # Effect size: small to medium (0 to 0.5 standard deviations)
            effect_size = np.random.choice([-1, 1]) * np.random.uniform(0, 0.5) * baseline_std
            introduce_inconsistency = np.random.random() < 0.25

            summary = generate_continuous_outcome(
                n_a, n_b, baseline_mean, baseline_std, effect_size, introduce_inconsistency
            )
            counts["continuous"] += 1

        # Add metadata
        summary["id"] = i
        summary["domain"] = np.random.choice(
            ["e-commerce", "healthcare", "finance", "technology", "education"]
        )
        summary["year"] = np.random.randint(2020, 2025)
        summary["source_url"] = f"https://example.com/test/{i}"

        summaries.append(summary)

    # Write outputs
    write_csv_output(summaries, output_dir / "synthetic_summaries.csv")
    write_json_output(summaries, output_dir / "synthetic_summaries.json")
    write_metadata(counts, n_total, seed, output_dir / "synthetic_metadata.json")

    logger.info(f"Generated {n_total} synthetic summaries: {counts['binary']} binary, {counts['continuous']} continuous")
    logger.info(f"Output written to {output_dir}")

    return summaries, counts


def verify_outcome_types(summaries: List[Dict[str, Any]]) -> Tuple[bool, Dict[str, int]]:
    """
    Verify that the dataset contains both binary and continuous outcomes.

    Args:
        summaries: List of generated summaries

    Returns:
        Tuple of (success flag, count by outcome type)
    """
    counts = {"binary": 0, "continuous": 0}
    for summary in summaries:
        outcome_type = summary.get("outcome_type")
        if outcome_type == "binary":
            counts["binary"] += 1
        elif outcome_type == "continuous":
            counts["continuous"] += 1

    has_both = counts["binary"] > 0 and counts["continuous"] > 0
    total = counts["binary"] + counts["continuous"]

    logger.info(f"Verification: {total} total summaries ({counts['binary']} binary, {counts['continuous']} continuous)")

    if not has_both:
        logger.error("Dataset must contain both binary and continuous outcomes")
        return False, counts

    return True, counts


def write_csv_output(summaries: List[Dict[str, Any]], filepath: Path) -> None:
    """Write summaries to CSV file."""
    if not summaries:
        logger.warning("No summaries to write to CSV")
        return

    fieldnames = list(summaries[0].keys())
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)
    logger.info(f"Wrote {len(summaries)} records to {filepath}")


def write_json_output(summaries: List[Dict[str, Any]], filepath: Path) -> None:
    """Write summaries to JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(summaries, f, indent=2)
    logger.info(f"Wrote {len(summaries)} records to {filepath}")


def write_metadata(counts: Dict[str, int], total: int, seed: int, filepath: Path) -> None:
    """Write generation metadata to JSON file."""
    metadata = {
        "total_records": total,
        "outcome_counts": counts,
        "seed": seed,
        "generated_at": datetime.now().isoformat(),
        "version": "1.0"
    }
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Metadata written to {filepath}")


def main() -> int:
    """Main entry point for synthetic dataset generation."""
    output_dir = Path("data/synthetic")
    n_total = 10000
    binary_ratio = 0.5
    seed = SEED

    logger.info(f"Starting synthetic dataset generation: {n_total} records, seed={seed}")

    try:
        summaries, counts = generate_synthetic_dataset(
            n_total=n_total,
            binary_ratio=binary_ratio,
            output_dir=output_dir,
            seed=seed
        )

        # Verify outcome types
        success, verified_counts = verify_outcome_types(summaries)

        if not success:
            logger.error("Verification failed: dataset must contain both outcome types")
            return 1

        # Verify minimum record count
        if len(summaries) < 10000:
            logger.error(f"Insufficient records: {len(summaries)} < 10000")
            return 1

        logger.info(f"SUCCESS: Generated {len(summaries)} valid synthetic summaries")
        logger.info(f"Outcome distribution: {verified_counts}")
        return 0

    except Exception as e:
        logger.error(f"Failed to generate synthetic dataset: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
