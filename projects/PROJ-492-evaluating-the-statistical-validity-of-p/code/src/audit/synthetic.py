"""
Synthetic Dataset Generator for A/B Test Validation (FR-030).

Generates a realistic synthetic corpus of A/B test summaries containing
both binary and continuous outcomes to validate the statistical audit pipeline.
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

from code.src.config import set_rng_seed, SEED
from code.src.utils.logger import get_default_logger, AuditLogger

# Constants for synthetic data generation
MIN_SAMPLES_CONTROL = 50
MAX_SAMPLES_CONTROL = 5000
MIN_SAMPLES_TREATMENT = 50
MAX_SAMPLES_TREATMENT = 5000
BASELINE_RATE_MIN = 0.01
BASELINE_RATE_MAX = 0.50
EFFECT_SIZE_MIN = 0.0
EFFECT_SIZE_MAX = 0.30
MEAN_CONTROL_MIN = 10.0
MEAN_CONTROL_MAX = 100.0
STD_DEV_MIN = 5.0
STD_DEV_MAX = 50.0
INCONSISTENCY_RATE = 0.15  # 15% of records will have intentional inconsistencies
TOTAL_RECORDS = 10500      # Ensure >= 10,000 records
BINARY_RATIO = 0.5         # 50% binary, 50% continuous


def set_all_seeds(seed: int = SEED) -> None:
    """Initialize random seeds for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)


def generate_sample_sizes() -> Tuple[int, int]:
    """Generate random sample sizes for control and treatment groups."""
    n_control = random.randint(MIN_SAMPLES_CONTROL, MAX_SAMPLES_CONTROL)
    n_treatment = random.randint(MIN_SAMPLES_TREATMENT, MAX_SAMPLES_TREATMENT)
    return n_control, n_treatment


def generate_binary_outcome(
    n_control: int,
    n_treatment: int,
    baseline_rate: float,
    effect_size: float,
    make_inconsistent: bool = False
) -> Dict[str, Any]:
    """
    Generate a synthetic binary outcome A/B test.

    Args:
        n_control: Sample size of control group.
        n_treatment: Sample size of treatment group.
        baseline_rate: Conversion rate of control group.
        effect_size: True effect size (lift).
        make_inconsistent: If True, introduce statistical inconsistency.

    Returns:
        Dictionary with metrics for the summary.
    """
    p_control = baseline_rate
    p_treatment = p_control * (1 + effect_size)

    # Clamp probabilities
    p_treatment = max(0.0, min(1.0, p_treatment))

    # Generate true counts
    x_control = np.random.binomial(n_control, p_control)
    x_treatment = np.random.binomial(n_treatment, p_treatment)

    observed_rate_control = x_control / n_control
    observed_rate_treatment = x_treatment / n_treatment

    # Calculate "reported" p-value and effect size
    # Standard two-proportion z-test
    p_pooled = (x_control + x_treatment) / (n_control + n_treatment)
    se = math.sqrt(p_pooled * (1 - p_pooled) * (1/n_control + 1/n_treatment))
    
    if se == 0:
        z_stat = 0.0
    else:
        z_stat = (observed_rate_treatment - observed_rate_control) / se

    true_p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    
    # Reported values
    if make_inconsistent:
        # Introduce inconsistency: report a p-value that doesn't match the stats
        # e.g., report p < 0.05 when it should be > 0.05, or vice versa
        # We'll shift the p-value by a factor
        reported_p_value = true_p_value * random.uniform(0.1, 10.0)
        reported_p_value = max(0.0, min(1.0, reported_p_value))
        reported_effect_size = observed_rate_treatment - observed_rate_control
        # Sometimes flip the sign of effect size for extreme inconsistency
        if random.random() < 0.1:
            reported_effect_size = -reported_effect_size
    else:
        reported_p_value = true_p_value
        reported_effect_size = observed_rate_treatment - observed_rate_control

    return {
        "outcome_type": "binary",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "successes_control": int(x_control),
        "successes_treatment": int(x_treatment),
        "rate_control": observed_rate_control,
        "rate_treatment": observed_rate_treatment,
        "reported_p_value": reported_p_value,
        "reported_effect_size": reported_effect_size,
        "true_p_value": true_p_value,
        "is_inconsistent": make_inconsistent
    }


def generate_continuous_outcome(
    n_control: int,
    n_treatment: int,
    mean_control: float,
    effect_size: float,
    std_dev: float,
    make_inconsistent: bool = False
) -> Dict[str, Any]:
    """
    Generate a synthetic continuous outcome A/B test.

    Args:
        n_control: Sample size of control group.
        n_treatment: Sample size of treatment group.
        mean_control: Mean of control group.
        effect_size: True effect size (lift in mean).
        std_dev: Standard deviation (assumed equal for simplicity).
        make_inconsistent: If True, introduce statistical inconsistency.

    Returns:
        Dictionary with metrics for the summary.
    """
    mean_treatment = mean_control * (1 + effect_size)
    
    # Generate data
    data_control = np.random.normal(mean_control, std_dev, n_control)
    data_treatment = np.random.normal(mean_treatment, std_dev, n_treatment)

    obs_mean_control = np.mean(data_control)
    obs_mean_treatment = np.mean(data_treatment)
    obs_std_control = np.std(data_control, ddof=1)
    obs_std_treatment = np.std(data_treatment, ddof=1)

    # Welch's t-test
    se_diff = math.sqrt((obs_std_control**2 / n_control) + (obs_std_treatment**2 / n_treatment))
    if se_diff == 0:
        t_stat = 0.0
        df = 1
    else:
        t_stat = (obs_mean_treatment - obs_mean_control) / se_diff
        # Welch-Satterthwaite equation for degrees of freedom
        num = (obs_std_control**2 / n_control + obs_std_treatment**2 / n_treatment)**2
        den = (obs_std_control**2 / n_control)**2 / (n_control - 1) + (obs_std_treatment**2 / n_treatment)**2 / (n_treatment - 1)
        df = num / den if den > 0 else 1

    true_p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df))

    # Reported values
    if make_inconsistent:
        reported_p_value = true_p_value * random.uniform(0.1, 10.0)
        reported_p_value = max(0.0, min(1.0, reported_p_value))
        reported_effect_size = obs_mean_treatment - obs_mean_control
        if random.random() < 0.1:
            reported_effect_size = -reported_effect_size
    else:
        reported_p_value = true_p_value
        reported_effect_size = obs_mean_treatment - obs_mean_control

    return {
        "outcome_type": "continuous",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "mean_control": obs_mean_control,
        "mean_treatment": obs_mean_treatment,
        "std_control": obs_std_control,
        "std_treatment": obs_std_treatment,
        "reported_p_value": reported_p_value,
        "reported_effect_size": reported_effect_size,
        "true_p_value": true_p_value,
        "is_inconsistent": make_inconsistent
    }


def generate_synthetic_dataset(
    total_records: int = TOTAL_RECORDS,
    binary_ratio: float = BINARY_RATIO,
    inconsistency_rate: float = INCONSISTENCY_RATE,
    seed: int = SEED
) -> List[Dict[str, Any]]:
    """
    Generate the full synthetic dataset.

    Args:
        total_records: Total number of records to generate.
        binary_ratio: Fraction of records that are binary outcomes.
        inconsistency_rate: Fraction of records with intentional inconsistencies.
        seed: Random seed.

    Returns:
        List of synthetic summary dictionaries.
    """
    set_all_seeds(seed)
    records = []
    num_binary = int(total_records * binary_ratio)
    num_continuous = total_records - num_binary

    for i in range(total_records):
        is_binary = i < num_binary
        is_inconsistent = random.random() < inconsistency_rate

        n_control, n_treatment = generate_sample_sizes()

        if is_binary:
            baseline = random.uniform(BASELINE_RATE_MIN, BASELINE_RATE_MAX)
            effect = random.uniform(EFFECT_SIZE_MIN, EFFECT_SIZE_MAX)
            record = generate_binary_outcome(
                n_control, n_treatment, baseline, effect, is_inconsistent
            )
        else:
            mean_c = random.uniform(MEAN_CONTROL_MIN, MEAN_CONTROL_MAX)
            effect = random.uniform(EFFECT_SIZE_MIN, EFFECT_SIZE_MAX)
            std = random.uniform(STD_DEV_MIN, STD_DEV_MAX)
            record = generate_continuous_outcome(
                n_control, n_treatment, mean_c, effect, std, is_inconsistent
            )

        # Add metadata
        record["id"] = f"syn_{i:06d}"
        record["generated_at"] = datetime.utcnow().isoformat()
        record["domain"] = random.choice(["tech", "finance", "health", "retail", "education"])
        
        records.append(record)

    return records


def write_csv_output(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Write synthetic dataset to CSV."""
    if not records:
        logging.warning("No records to write.")
        return

    # Flatten nested dicts if necessary, but our structure is flat enough
    fieldnames = list(records[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def write_json_output(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Write synthetic dataset to JSON."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, default=str)


def write_metadata(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Write generation metadata."""
    binary_count = sum(1 for r in records if r["outcome_type"] == "binary")
    continuous_count = sum(1 for r in records if r["outcome_type"] == "continuous")
    inconsistent_count = sum(1 for r in records if r["is_inconsistent"])

    metadata = {
        "total_records": len(records),
        "binary_outcomes": binary_count,
        "continuous_outcomes": continuous_count,
        "inconsistent_records": inconsistent_count,
        "generation_timestamp": datetime.utcnow().isoformat(),
        "seed": SEED
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)


def verify_outcome_types(records: List[Dict[str, Any]]) -> Tuple[int, int]:
    """Verify that both outcome types are present."""
    binary = sum(1 for r in records if r["outcome_type"] == "binary")
    continuous = sum(1 for r in records if r["outcome_type"] == "continuous")
    return binary, continuous


def main() -> None:
    """Main entry point for synthetic dataset generation."""
    logger = get_default_logger()
    logger.info("Starting synthetic dataset generation (T026)...")

    # Paths
    data_dir = Path("code/data/synthetic")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    csv_path = data_dir / "synthetic_summaries.csv"
    json_path = data_dir / "synthetic_summaries.json"
    metadata_path = data_dir / "synthetic_metadata.json"

    # Generate
    logger.info(f"Generating {TOTAL_RECORDS} synthetic records...")
    records = generate_synthetic_dataset(
        total_records=TOTAL_RECORDS,
        binary_ratio=BINARY_RATIO,
        inconsistency_rate=INCONSISTENCY_RATE,
        seed=SEED
    )

    # Verify
    binary_count, continuous_count = verify_outcome_types(records)
    logger.info(f"Generated {len(records)} records: {binary_count} binary, {continuous_count} continuous")

    if binary_count == 0 or continuous_count == 0:
        raise ValueError("Verification failed: Both outcome types must be present.")

    if len(records) < 10000:
        raise ValueError(f"Verification failed: Expected >= 10000 records, got {len(records)}")

    # Write outputs
    logger.info(f"Writing CSV to {csv_path}...")
    write_csv_output(records, csv_path)

    logger.info(f"Writing JSON to {json_path}...")
    write_json_output(records, json_path)

    logger.info(f"Writing metadata to {metadata_path}...")
    write_metadata(records, metadata_path)

    logger.info("Synthetic dataset generation completed successfully.")


if __name__ == "__main__":
    main()
