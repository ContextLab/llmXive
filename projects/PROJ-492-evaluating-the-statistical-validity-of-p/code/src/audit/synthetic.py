"""
Synthetic Dataset Generator for A/B Test Audit Validation (FR-030)

Generates a large corpus of simulated A/B test summaries with both binary
and continuous outcomes to validate the statistical consistency pipeline.
"""
import csv
import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
from scipy import stats

# Import from project utilities
from code.src.config import set_rng_seed, SEED
from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.models.data_models import ABTestSummary

# Configure logging
logger = get_default_logger(__name__)


def set_all_seeds(seed: int = SEED) -> None:
    """Initialize random seeds for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"All random seeds set to {seed}")


def generate_sample_sizes(min_n: int = 50, max_n: int = 10000) -> Tuple[int, int]:
    """
    Generate realistic sample sizes for control and treatment groups.
    Uses a log-uniform distribution to mimic real-world variance.
    """
    n_control = int(np.random.lognormal(mean=6.0, sigma=1.0))
    n_control = max(min_n, min(max_n, n_control))

    # Treatment size is usually similar to control, +/- 20%
    ratio = np.random.uniform(0.8, 1.2)
    n_treatment = int(n_control * ratio)
    n_treatment = max(min_n, min(max_n, n_treatment))

    return n_control, n_treatment


def generate_binary_outcome(
    n_control: int,
    n_treatment: int,
    baseline_rate: float,
    effect_size: float,
    seed: int
) -> Dict[str, Any]:
    """
    Generate synthetic binary outcome data (conversion rates).

    Args:
        n_control: Sample size for control group
        n_treatment: Sample size for treatment group
        baseline_rate: True conversion rate for control (0.0 - 1.0)
        effect_size: Relative lift (e.g., 0.1 for 10% increase) or negative for decrease
        seed: Random seed for this specific generation

    Returns:
        Dictionary with observed successes, rates, and true parameters
    """
    rng = np.random.default_rng(seed)

    # True rates
    p_control = baseline_rate
    p_treatment = baseline_rate * (1.0 + effect_size)
    # Clamp to valid probability
    p_treatment = max(0.0, min(1.0, p_treatment))

    # Generate successes (Binomial distribution)
    successes_control = rng.binomial(n_control, p_control)
    successes_treatment = rng.binomial(n_treatment, p_treatment)

    observed_rate_control = successes_control / n_control
    observed_rate_treatment = successes_treatment / n_treatment

    # Calculate z-statistic and p-value for two-proportion test
    # Using pooled proportion for standard error
    p_pooled = (successes_control + successes_treatment) / (n_control + n_treatment)
    if p_pooled == 0 or p_pooled == 1:
        p_value = 1.0
        z_stat = 0.0
    else:
        se = np.sqrt(p_pooled * (1 - p_pooled) * (1/n_control + 1/n_treatment))
        if se == 0:
            z_stat = 0.0
            p_value = 1.0
        else:
            z_stat = (observed_rate_treatment - observed_rate_control) / se
            p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))

    return {
        "outcome_type": "binary",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "successes_control": int(successes_control),
        "successes_treatment": int(successes_treatment),
        "rate_control": observed_rate_control,
        "rate_treatment": observed_rate_treatment,
        "true_p_control": p_control,
        "true_p_treatment": p_treatment,
        "true_effect_size": effect_size,
        "z_stat": float(z_stat),
        "p_value": float(p_value)
    }


def generate_continuous_outcome(
    n_control: int,
    n_treatment: int,
    baseline_mean: float,
    baseline_std: float,
    effect_size: float,
    seed: int
) -> Dict[str, Any]:
    """
    Generate synthetic continuous outcome data (e.g., time on site, revenue).

    Args:
        n_control: Sample size for control group
        n_treatment: Sample size for treatment group
        baseline_mean: True mean for control group
        baseline_std: True standard deviation for control group
        effect_size: Absolute difference in means (treatment - control)
        seed: Random seed for this specific generation

    Returns:
        Dictionary with observed means, stds, and true parameters
    """
    rng = np.random.default_rng(seed)

    # True parameters
    mu_control = baseline_mean
    sigma_control = baseline_std
    mu_treatment = baseline_mean + effect_size
    sigma_treatment = baseline_std * np.random.uniform(0.9, 1.1) # Slight variance shift

    # Generate samples
    samples_control = rng.normal(mu_control, sigma_control, n_control)
    samples_treatment = rng.normal(mu_treatment, sigma_treatment, n_treatment)

    # Observed statistics
    obs_mean_control = float(np.mean(samples_control))
    obs_mean_treatment = float(np.mean(samples_treatment))
    obs_std_control = float(np.std(samples_control, ddof=1))
    obs_std_treatment = float(np.std(samples_treatment, ddof=1))

    # Welch's t-test
    t_stat, p_value = stats.ttest_ind(
        samples_control, samples_treatment, equal_var=False
    )

    return {
        "outcome_type": "continuous",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "mean_control": obs_mean_control,
        "mean_treatment": obs_mean_treatment,
        "std_control": obs_std_control,
        "std_treatment": obs_std_treatment,
        "true_mean_control": mu_control,
        "true_mean_treatment": mu_treatment,
        "true_effect_size": effect_size,
        "t_stat": float(t_stat),
        "p_value": float(p_value)
    }


def generate_synthetic_dataset(
    total_records: int = 10000,
    binary_ratio: float = 0.5,
    output_dir: Path = None
) -> List[Dict[str, Any]]:
    """
    Generate the full synthetic dataset.

    Args:
        total_records: Total number of summaries to generate (>= 10,000)
        binary_ratio: Proportion of records that are binary outcomes
        output_dir: Directory to write output files

    Returns:
        List of generated summary dictionaries
    """
    if output_dir is None:
        output_dir = Path("code/data/synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)

    set_all_seeds()

    records = []
    binary_count = 0
    continuous_count = 0

    logger.info(f"Generating {total_records} synthetic summaries...")

    # Define parameter distributions
    # Binary: baseline rates between 0.01 and 0.5, effects between -0.2 and 0.5
    # Continuous: means between 10 and 1000, stds between 1 and 200, effects between -50 and 50

    for i in range(total_records):
        is_binary = random.random() < binary_ratio
        seed = i * 12345 + SEED # Deterministic seed per record

        if is_binary:
            n_c, n_t = generate_sample_sizes()
            base_rate = np.random.uniform(0.01, 0.5)
            # Effect size: 50% chance of null, 50% chance of non-null
            if random.random() < 0.5:
                effect = 0.0
            else:
                effect = np.random.choice([-1, 1]) * np.random.uniform(0.01, 0.2)

            record = generate_binary_outcome(n_c, n_t, base_rate, effect, seed)
            binary_count += 1
        else:
            n_c, n_t = generate_sample_sizes()
            base_mean = np.random.uniform(10.0, 1000.0)
            base_std = base_mean * np.random.uniform(0.1, 0.5) # CV between 0.1 and 0.5
            if random.random() < 0.5:
                effect = 0.0
            else:
                effect = np.random.choice([-1, 1]) * base_mean * np.random.uniform(0.01, 0.2)

            record = generate_continuous_outcome(n_c, n_t, base_mean, base_std, effect, seed)
            continuous_count += 1

        # Add metadata
        record["id"] = f"synth_{i:06d}"
        record["generated_at"] = datetime.utcnow().isoformat()
        record["seed"] = seed

        records.append(record)

    # Verification
    logger.info(f"Generation complete. Binary: {binary_count}, Continuous: {continuous_count}")
    if binary_count == 0 or continuous_count == 0:
        raise ValueError("Both binary and continuous outcomes must be present.")

    # Write CSV
    csv_path = output_dir / "synthetic_summaries.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        # Flatten nested dicts for CSV
        if records:
            fieldnames = list(records[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)

    logger.info(f"Wrote {len(records)} records to {csv_path}")

    # Write metadata JSON
    meta_path = output_dir / "synthetic_metadata.json"
    metadata = {
        "total_records": total_records,
        "binary_count": binary_count,
        "continuous_count": continuous_count,
        "binary_ratio": binary_ratio,
        "generation_seed": SEED,
        "generated_at": datetime.utcnow().isoformat(),
        "file_path": str(csv_path)
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Wrote metadata to {meta_path}")

    return records


def verify_outcome_types(records: List[Dict[str, Any]]) -> Tuple[int, int]:
    """Verify that both outcome types are present in the dataset."""
    binary = sum(1 for r in records if r.get("outcome_type") == "binary")
    continuous = sum(1 for r in records if r.get("outcome_type") == "continuous")

    if binary == 0:
        raise ValueError("Verification failed: No binary outcomes found.")
    if continuous == 0:
        raise ValueError("Verification failed: No continuous outcomes found.")

    return binary, continuous


def write_metadata(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Write summary metadata to a JSON file."""
    binary_count, continuous_count = verify_outcome_types(records)
    meta = {
        "total_count": len(records),
        "binary_count": binary_count,
        "continuous_count": continuous_count,
        "timestamp": datetime.utcnow().isoformat()
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    logger.info(f"Wrote metadata to {output_path}")


def main() -> None:
    """Entry point for synthetic dataset generation."""
    logger.info("Starting synthetic dataset generation (Task T026)...")

    output_dir = Path("code/data/synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate at least 10,000 records as per FR-030
    total_records = 10000
    binary_ratio = 0.5 # 50% binary, 50% continuous

    try:
        records = generate_synthetic_dataset(
            total_records=total_records,
            binary_ratio=binary_ratio,
            output_dir=output_dir
        )

        # Verify
        binary_count, continuous_count = verify_outcome_types(records)
        logger.info(f"Verification passed: {binary_count} binary, {continuous_count} continuous")

        if len(records) < total_records:
            logger.error(f"Generated {len(records)} records, expected {total_records}")
            return 1

        logger.info("Synthetic dataset generation completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Synthetic dataset generation failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
