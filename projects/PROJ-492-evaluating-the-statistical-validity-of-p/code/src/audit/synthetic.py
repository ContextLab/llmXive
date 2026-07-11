"""
Synthetic Dataset Generator for A/B Test Validity Evaluation (FR-030).

Generates a large-scale synthetic dataset of A/B test summaries with
known ground truth to validate the statistical reconstruction and
inconsistency detection pipeline.

Supports both binary (proportion) and continuous (mean difference) outcomes.
Ensures constraint preservation:
  - Some records are statistically consistent (p_recon ≈ p_reported).
  - Some records are intentionally inconsistent (p_recon != p_reported) to test detection.
  - Sample sizes are realistic and varied.
  - Domain and year metadata are included for subgroup analysis.
"""

import csv
import json
import logging
import math
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
from scipy import stats

from code.src.config import SEED, set_rng_seed
from code.src.models.data_models import ABTestSummary
from code.src.utils.logger import get_default_logger

# Configuration
DEFAULT_SEED = SEED
TOTAL_RECORDS = 10000
BINARY_RATIO = 0.6  # 60% binary outcomes, 40% continuous
INCONSISTENCY_RATE = 0.15  # 15% of records will have intentional statistical inconsistencies

# Realistic parameter ranges
MIN_SAMPLE_SIZE = 100
MAX_SAMPLE_SIZE = 50000
BASELINE_PROPORTION_MIN = 0.01
BASELINE_PROPORTION_MAX = 0.50
EFFECT_SIZE_BINARY_MIN = 0.001
EFFECT_SIZE_BINARY_MAX = 0.10
BASELINE_MEAN_MIN = 10.0
BASELINE_MEAN_MAX = 100.0
STD_DEV_MIN = 5.0
STD_DEV_MAX = 50.0
EFFECT_SIZE_CONTINUOUS_MIN = 0.5
EFFECT_SIZE_CONTINUOUS_MAX = 5.0

# Domains for realism
DOMAINS = [
    "e-commerce", "fintech", "healthcare", "education", "media",
    "travel", "gaming", "social", "advertising", "saas"
]

logger = get_default_logger(__name__)


def set_all_seeds(seed: int = DEFAULT_SEED) -> None:
    """Set global random seeds for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Seeds initialized with {seed}")


def generate_sample_sizes(n: int) -> List[int]:
    """Generate realistic sample sizes following a log-normal distribution."""
    # Most tests have moderate sample sizes, few have very large ones
    mean_log = math.log(1000)
    std_log = 1.0
    sizes = np.random.lognormal(mean_log, std_log, n).astype(int)
    sizes = np.clip(sizes, MIN_SAMPLE_SIZE, MAX_SAMPLE_SIZE)
    return sizes.tolist()


def generate_binary_outcome(
    n_control: int,
    n_treatment: int,
    baseline_p: float,
    effect_size: float,
    is_inconsistent: bool = False
) -> Tuple[Dict[str, Any], float]:
    """
    Generate a binary outcome A/B test summary.

    Returns:
        summary_dict: Dictionary with control/treatment counts and proportions.
        true_p_value: The actual p-value from the generated data (for validation).
    """
    p_control = baseline_p
    p_treatment = baseline_p + effect_size
    p_treatment = max(0.0, min(1.0, p_treatment))

    # Generate actual counts based on probabilities
    successes_control = np.random.binomial(n_control, p_control)
    successes_treatment = np.random.binomial(n_treatment, p_treatment)

    prop_control = successes_control / n_control
    prop_treatment = successes_treatment / n_treatment

    # Calculate true p-value using two-proportion z-test
    try:
        z_stat, true_p_value = stats.proportions_ztest(
            [successes_control, successes_treatment],
            [n_control, n_treatment]
        )
    except Exception:
        true_p_value = 1.0

    # Introduce inconsistency if requested
    if is_inconsistent:
        # Artificially inflate or deflate the reported p-value
        # by a significant margin (> 0.05 absolute difference)
        if random.random() < 0.5:
            reported_p = max(0.01, true_p_value - random.uniform(0.06, 0.15))
        else:
            reported_p = min(0.99, true_p_value + random.uniform(0.06, 0.15))
    else:
        reported_p = true_p_value

    return {
        "outcome_type": "binary",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "successes_control": int(successes_control),
        "successes_treatment": int(successes_treatment),
        "proportion_control": round(prop_control, 6),
        "proportion_treatment": round(prop_treatment, 6),
        "effect_size": round(prop_treatment - prop_control, 6),
        "reported_p_value": round(reported_p, 6),
        "true_p_value": round(true_p_value, 6),
        "is_inconsistent": is_inconsistent
    }, true_p_value


def generate_continuous_outcome(
    n_control: int,
    n_treatment: int,
    mean_control: float,
    std_control: float,
    mean_treatment: float,
    std_treatment: float,
    is_inconsistent: bool = False
) -> Tuple[Dict[str, Any], float]:
    """
    Generate a continuous outcome A/B test summary.

    Returns:
        summary_dict: Dictionary with means, std devs, and sample sizes.
        true_p_value: The actual p-value from the generated data.
    """
    # Generate synthetic data points (only for p-value calculation, not stored)
    data_control = np.random.normal(mean_control, std_control, n_control)
    data_treatment = np.random.normal(mean_treatment, std_treatment, n_treatment)

    # Calculate summary statistics
    mean_c = float(np.mean(data_control))
    mean_t = float(np.mean(data_treatment))
    std_c = float(np.std(data_control, ddof=1))
    std_t = float(np.std(data_treatment, ddof=1))

    # Calculate true p-value using Welch's t-test
    try:
        t_stat, true_p_value = stats.ttest_ind(
            data_control, data_treatment, equal_var=False
        )
    except Exception:
        true_p_value = 1.0

    # Introduce inconsistency
    if is_inconsistent:
        if random.random() < 0.5:
            reported_p = max(0.01, true_p_value - random.uniform(0.06, 0.15))
        else:
            reported_p = min(0.99, true_p_value + random.uniform(0.06, 0.15))
    else:
        reported_p = true_p_value

    return {
        "outcome_type": "continuous",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "mean_control": round(mean_c, 4),
        "mean_treatment": round(mean_t, 4),
        "std_control": round(std_c, 4),
        "std_treatment": round(std_t, 4),
        "effect_size": round(mean_t - mean_c, 4),
        "reported_p_value": round(reported_p, 6),
        "true_p_value": round(true_p_value, 6),
        "is_inconsistent": is_inconsistent
    }, true_p_value


def generate_synthetic_dataset(
    n_records: int = TOTAL_RECORDS,
    seed: int = DEFAULT_SEED
) -> List[Dict[str, Any]]:
    """
    Generate the full synthetic dataset.

    Args:
        n_records: Total number of records to generate.
        seed: Random seed for reproducibility.

    Returns:
        List of dictionaries representing A/B test summaries.
    """
    set_all_seeds(seed)
    records = []

    logger.info(f"Generating {n_records} synthetic records...")

    # Pre-generate sample sizes and metadata
    sample_sizes = generate_sample_sizes(n_records)
    domains = [random.choice(DOMAINS) for _ in range(n_records)]
    years = [random.randint(2018, 2025) for _ in range(n_records)]

    for i in range(n_records):
        n_control, n_treatment = sample_sizes[i]
        domain = domains[i]
        year = years[i]

        # Decide outcome type
        is_binary = random.random() < BINARY_RATIO
        is_inconsistent = random.random() < INCONSISTENCY_RATE

        if is_binary:
            baseline_p = random.uniform(BASELINE_PROPORTION_MIN, BASELINE_PROPORTION_MAX)
            effect = random.uniform(EFFECT_SIZE_BINARY_MIN, EFFECT_SIZE_BINARY_MAX) * random.choice([-1, 1])
            record, _ = generate_binary_outcome(
                n_control, n_treatment, baseline_p, effect, is_inconsistent
            )
        else:
            mean_c = random.uniform(BASELINE_MEAN_MIN, BASELINE_MEAN_MAX)
            std_c = random.uniform(STD_DEV_MIN, STD_DEV_MAX)
            effect = random.uniform(EFFECT_SIZE_CONTINUOUS_MIN, EFFECT_SIZE_CONTINUOUS_MAX) * random.choice([-1, 1])
            mean_t = mean_c + effect
            std_t = std_c * random.uniform(0.8, 1.2)  # Slight variation in std dev
            record, _ = generate_continuous_outcome(
                n_control, n_treatment, mean_c, std_c, mean_t, std_t, is_inconsistent
            )

        # Add metadata
        record["domain"] = domain
        record["year"] = year
        record["id"] = f"synthetic_{i:06d}"
        record["timestamp"] = datetime.now().isoformat()

        records.append(record)

    logger.info(f"Generated {len(records)} records successfully.")
    return records


def verify_outcome_types(records: List[Dict[str, Any]]) -> Dict[str, int]:
    """Verify the distribution of outcome types in the dataset."""
    counts = {"binary": 0, "continuous": 0, "total": len(records)}
    for r in records:
        if r.get("outcome_type") == "binary":
            counts["binary"] += 1
        elif r.get("outcome_type") == "continuous":
            counts["continuous"] += 1
    return counts


def write_summaries_to_csv(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Write the synthetic dataset to a CSV file."""
    if not records:
        raise ValueError("No records to write.")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Flatten nested structures if any (though our generation is flat)
    fieldnames = list(records[0].keys())

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    logger.info(f"Written {len(records)} records to {output_path}")


def write_metadata(metadata: Dict[str, Any], output_path: Path) -> None:
    """Write generation metadata to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Written metadata to {output_path}")


def main() -> None:
    """Main entry point for generating the synthetic dataset."""
    output_dir = Path("code/data/synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "synthetic_ab_tests.csv"
    metadata_path = output_dir / "generation_metadata.json"

    try:
        records = generate_synthetic_dataset(n_records=TOTAL_RECORDS, seed=DEFAULT_SEED)

        # Verify constraints
        type_counts = verify_outcome_types(records)
        inconsistency_count = sum(1 for r in records if r.get("is_inconsistent", False))

        metadata = {
            "generated_at": datetime.now().isoformat(),
            "seed": DEFAULT_SEED,
            "total_records": len(records),
            "outcome_distribution": type_counts,
            "inconsistency_rate": inconsistency_count / len(records),
            "domains": list(set(r["domain"] for r in records)),
            "years": sorted(list(set(r["year"] for r in records)))
        }

        write_summaries_to_csv(records, csv_path)
        write_metadata(metadata, metadata_path)

        logger.info("Synthetic dataset generation completed successfully.")
        logger.info(f"Total records: {len(records)}")
        logger.info(f"Binary: {type_counts['binary']}, Continuous: {type_counts['continuous']}")
        logger.info(f"Inconsistent records: {inconsistency_count} ({inconsistency_count/len(records)*100:.1f}%)")

    except Exception as e:
        logger.error(f"Failed to generate synthetic dataset: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
