"""
Synthetic dataset generator for A/B test validation (FR-030).

Generates at least 10,000 simulated summaries covering both binary and continuous
outcomes. Outputs are written to data/synthetic_summaries.csv and data/synthetic_summaries.json.
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

from code.src.config import SEED, set_rng_seed
from code.src.models.data_models import ABTestSummary
from code.src.utils.logger import get_default_logger

logger = get_default_logger(__name__)

# Constants for generation
MIN_BINARY_SAMPLE = 100
MAX_BINARY_SAMPLE = 5000
MIN_CONTINUOUS_SAMPLE = 50
MAX_CONTINUOUS_SAMPLE = 2000
BINARY_BASELINE_MIN = 0.01
BINARY_BASELINE_MAX = 0.50
CONTINUOUS_MEAN_MIN = 0.0
CONTINUOUS_MEAN_MAX = 100.0
CONTINUOUS_STD_MIN = 5.0
CONTINUOUS_STD_MAX = 30.0
EFFECT_SIZE_MIN = 0.01
EFFECT_SIZE_MAX = 0.20
ALPHA = 0.05
TOTAL_RECORDS = 10500  # Slightly above 10k to ensure threshold
BINARY_RATIO = 0.5  # 50% binary, 50% continuous


def set_all_seeds(seed: int = SEED) -> None:
    """Seed all random number generators for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Random seeds set to {seed}")


def generate_sample_sizes(is_binary: bool) -> Tuple[int, int]:
    """
    Generate sample sizes for control (n1) and treatment (n2) groups.
    Ensures some mismatch scenarios for testing validator (T025).
    """
    if is_binary:
        n1 = random.randint(MIN_BINARY_SAMPLE, MAX_BINARY_SAMPLE)
        # 95% chance of matching, 5% chance of mismatch for testing
        if random.random() < 0.95:
            n2 = n1
        else:
            n2 = n1 + random.randint(-50, 50)
    else:
        n1 = random.randint(MIN_CONTINUOUS_SAMPLE, MAX_CONTINUOUS_SAMPLE)
        if random.random() < 0.95:
            n2 = n1
        else:
            n2 = n1 + random.randint(-20, 20)

    return n1, n2


def generate_binary_outcome() -> Dict[str, Any]:
    """
    Generate a synthetic binary outcome A/B test summary.
    Simulates a two-proportion z-test scenario.
    """
    n1, n2 = generate_sample_sizes(is_binary=True)
    p1 = random.uniform(BINARY_BASELINE_MIN, BINARY_BASELINE_MAX)

    # Determine effect direction and magnitude
    effect = random.uniform(EFFECT_SIZE_MIN, EFFECT_SIZE_MAX)
    if random.random() < 0.5:
        p2 = p1 + effect
    else:
        p2 = max(0.0, p1 - effect)

    # Ensure p2 stays within valid probability range
    p2 = max(0.0, min(1.0, p2))

    # Calculate expected successes (rounded)
    x1 = int(round(n1 * p1))
    x2 = int(round(n2 * p2))

    # Add small noise to counts to simulate real-world reporting variance
    if random.random() < 0.1:
        x1 = max(0, x1 + random.choice([-1, 1]))
        x2 = max(0, x2 + random.choice([-1, 1]))

    # Calculate reported p-value with slight noise to simulate rounding/reporting
    # We compute the "true" p-value first, then add noise
    pooled_p = (x1 + x2) / (n1 + n2)
    if pooled_p == 0 or pooled_p == 1:
        true_p = 1.0
    else:
        se = math.sqrt(pooled_p * (1 - pooled_p) * (1/n1 + 1/n2))
        if se == 0:
            z_stat = 0.0
        else:
            z_stat = (p1 - p2) / se
        true_p = 2 * (1 - 0.5 * (1 + math.erf(abs(z_stat) / math.sqrt(2))))

    # Add reporting noise (rounding to 3-4 decimal places often seen)
    noise = random.uniform(-0.005, 0.005)
    reported_p = max(0.0, min(1.0, true_p + noise))
    reported_p = round(reported_p, 4)

    return {
        "outcome_type": "binary",
        "n_control": n1,
        "n_treatment": n2,
        "p_control": round(p1, 4),
        "p_treatment": round(p2, 4),
        "successes_control": x1,
        "successes_treatment": x2,
        "reported_p_value": reported_p,
        "effect_size": round(p2 - p1, 4)
    }


def generate_continuous_outcome() -> Dict[str, Any]:
    """
    Generate a synthetic continuous outcome A/B test summary.
    Simulates a Welch's t-test scenario.
    """
    n1, n2 = generate_sample_sizes(is_binary=False)
    mean1 = random.uniform(CONTINUOUS_MEAN_MIN, CONTINUOUS_MEAN_MAX)
    std1 = random.uniform(CONTINUOUS_STD_MIN, CONTINUOUS_STD_MAX)

    # Determine effect size in terms of standard deviation (Cohen's d approx)
    d = random.uniform(EFFECT_SIZE_MIN, EFFECT_SIZE_MAX)
    if random.random() < 0.5:
        mean2 = mean1 + d * std1
    else:
        mean2 = mean1 - d * std1

    std2 = std1 * random.uniform(0.8, 1.2)  # Allow some variance difference

    # Calculate t-statistic and p-value
    se_diff = math.sqrt((std1**2 / n1) + (std2**2 / n2))
    if se_diff == 0:
        t_stat = 0.0
    else:
        t_stat = (mean1 - mean2) / se_diff

    # Welch-Satterthwaite degrees of freedom
    num = (std1**2 / n1 + std2**2 / n2)**2
    den = ((std1**2 / n1)**2 / (n1 - 1)) + ((std2**2 / n2)**2 / (n2 - 1))
    if den == 0:
        df = 1
    else:
        df = num / den

    # Approximate p-value using normal approximation for large df
    # For small df, this is approximate but sufficient for synthetic data generation
    p_val = 2 * (1 - 0.5 * (1 + math.erf(abs(t_stat) / math.sqrt(2))))

    # Add reporting noise
    noise = random.uniform(-0.005, 0.005)
    reported_p = max(0.0, min(1.0, p_val + noise))
    reported_p = round(reported_p, 4)

    return {
        "outcome_type": "continuous",
        "n_control": n1,
        "n_treatment": n2,
        "mean_control": round(mean1, 4),
        "mean_treatment": round(mean2, 4),
        "std_control": round(std1, 4),
        "std_treatment": round(std2, 4),
        "reported_p_value": reported_p,
        "effect_size": round(mean2 - mean1, 4)
    }


def generate_synthetic_dataset(total_records: int = TOTAL_RECORDS) -> List[Dict[str, Any]]:
    """
    Generate the full synthetic dataset with mixed outcome types.
    """
    set_all_seeds()
    records = []

    # Calculate target counts for each type
    binary_count = int(total_records * BINARY_RATIO)
    continuous_count = total_records - binary_count

    logger.info(f"Generating {binary_count} binary and {continuous_count} continuous records")

    for i in range(binary_count):
        record = generate_binary_outcome()
        record["id"] = f"syn_bin_{i:06d}"
        record["domain"] = random.choice(["tech", "health", "finance", "retail", "education"])
        record["year"] = random.randint(2018, 2024)
        records.append(record)

    for i in range(continuous_count):
        record = generate_continuous_outcome()
        record["id"] = f"syn_cont_{i:06d}"
        record["domain"] = random.choice(["tech", "health", "finance", "retail", "education"])
        record["year"] = random.randint(2018, 2024)
        records.append(record)

    # Shuffle to mix types
    random.shuffle(records)
    return records


def write_csv_output(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Write synthetic records to CSV."""
    if not records:
        logger.warning("No records to write to CSV")
        return

    # Flatten nested dicts if any, but our records are flat
    fieldnames = list(records[0].keys())

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    logger.info(f"Wrote {len(records)} records to {output_path}")


def write_json_output(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Write synthetic records to JSON."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, default=str)

    logger.info(f"Wrote {len(records)} records to {output_path}")


def verify_outcome_types(records: List[Dict[str, Any]]) -> Tuple[int, int]:
    """
    Verify that both binary and continuous outcomes are present.
    Returns (binary_count, continuous_count).
    """
    binary_count = sum(1 for r in records if r.get("outcome_type") == "binary")
    continuous_count = sum(1 for r in records if r.get("outcome_type") == "continuous")

    logger.info(f"Verification: {binary_count} binary, {continuous_count} continuous")

    if binary_count == 0:
        raise ValueError("No binary outcomes generated")
    if continuous_count == 0:
        raise ValueError("No continuous outcomes generated")

    return binary_count, continuous_count


def main() -> None:
    """Main entry point for synthetic dataset generation."""
    logger.info("Starting synthetic dataset generation (T026)")

    # Ensure output directory exists
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)

    csv_path = output_dir / "synthetic_summaries.csv"
    json_path = output_dir / "synthetic_summaries.json"

    # Generate data
    records = generate_synthetic_dataset(TOTAL_RECORDS)

    # Verify outcome types
    binary_count, continuous_count = verify_outcome_types(records)
    total = binary_count + continuous_count

    if total < 10000:
        raise ValueError(f"Generated {total} records, expected at least 10,000")

    logger.info(f"Generated {total} records (binary: {binary_count}, continuous: {continuous_count})")

    # Write outputs
    write_csv_output(records, csv_path)
    write_json_output(records, json_path)

    logger.info("Synthetic dataset generation completed successfully")


if __name__ == "__main__":
    main()
