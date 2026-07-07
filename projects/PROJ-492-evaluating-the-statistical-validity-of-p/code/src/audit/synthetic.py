"""
Synthetic Dataset Generator (FR-030)

Generates a synthetic dataset of at least 10,000 simulated A/B test summaries
containing both binary and continuous outcomes for validation purposes.
"""
import csv
import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import numpy as np

from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger

# Constants for generation
TOTAL_RECORDS = 10000
BINARY_RATIO = 0.5  # 50% binary, 50% continuous
BASELINE_RATES = [0.1, 0.2, 0.3, 0.4, 0.5]
EFFECT_SIZES = [0.01, 0.02, 0.05, 0.1]  # Absolute difference
MIN_SAMPLE_SIZE = 100
MAX_SAMPLE_SIZE = 10000
DOMAINS = ["tech", "finance", "health", "ecommerce", "education"]
YEARS = list(range(2018, 2025))

logger = get_default_logger(__name__)


def set_all_seeds(seed: int = SEED) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Seeds set to {seed}")


def generate_sample_sizes(n: int) -> Tuple[int, int]:
    """Generate sample sizes for control and treatment groups."""
    # Ensure n1 and n2 are roughly similar but not identical to allow for statistical variance
    base_n = max(MIN_SAMPLE_SIZE, int(np.random.normal(n, n * 0.2)))
    n1 = max(MIN_SAMPLE_SIZE, base_n)
    n2 = max(MIN_SAMPLE_SIZE, int(base_n * np.random.uniform(0.8, 1.2)))
    return n1, n2


def generate_binary_outcome(
    baseline_rate: float, effect_size: float, n1: int, n2: int
) -> Dict[str, Any]:
    """
    Generate a synthetic binary A/B test summary.
    Simulates conversions based on binomial distribution.
    """
    p_control = baseline_rate
    p_treatment = baseline_rate + effect_size
    # Ensure probability stays within [0, 1]
    p_treatment = max(0.0, min(1.0, p_treatment))

    # Simulate successes
    x1 = np.random.binomial(n1, p_control)
    x2 = np.random.binomial(n2, p_treatment)

    # Calculate observed rates
    rate_control = x1 / n1 if n1 > 0 else 0.0
    rate_treatment = x2 / n2 if n2 > 0 else 0.0

    # Calculate p-value using two-proportion z-test approximation
    # p_pool = (x1 + x2) / (n1 + n2)
    # se = np.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
    # z = (rate_treatment - rate_control) / se if se > 0 else 0.0
    # p_value = 2 * (1 - stats.norm.cdf(abs(z)))

    # For synthetic generation, we use the theoretical p-value based on effect size
    # to ensure consistency, then add slight noise to simulate real-world variance
    # if needed, but for this task, we compute the exact statistical values
    # based on the generated counts.
    from scipy import stats

    p_pool = (x1 + x2) / (n1 + n2) if (n1 + n2) > 0 else 0
    se = np.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2)) if p_pool > 0 and p_pool < 1 else 1e-9
    z_score = (rate_treatment - rate_control) / se if se > 1e-9 else 0.0
    p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))

    return {
        "outcome_type": "binary",
        "n_control": n1,
        "n_treatment": n2,
        "successes_control": int(x1),
        "successes_treatment": int(x2),
        "rate_control": rate_control,
        "rate_treatment": rate_treatment,
        "p_value": p_value,
        "effect_size": rate_treatment - rate_control,
    }


def generate_continuous_outcome(
    baseline_mean: float, effect_size: float, n1: int, n2: int, std_dev: float = 1.0
) -> Dict[str, Any]:
    """
    Generate a synthetic continuous A/B test summary.
    Simulates means based on normal distribution.
    """
    mu_control = baseline_mean
    mu_treatment = baseline_mean + effect_size

    # Simulate samples
    sample_control = np.random.normal(mu_control, std_dev, n1)
    sample_treatment = np.random.normal(mu_treatment, std_dev, n2)

    mean_control = np.mean(sample_control)
    mean_treatment = np.mean(sample_treatment)

    std_control = np.std(sample_control, ddof=1)
    std_treatment = np.std(sample_treatment, ddof=1)

    # Welch's t-test
    if std_control == 0 and std_treatment == 0:
        t_stat = 0.0
        p_value = 1.0
    else:
        t_stat, p_value = stats.ttest_ind(
            sample_control, sample_treatment, equal_var=False
        )

    return {
        "outcome_type": "continuous",
        "n_control": n1,
        "n_treatment": n2,
        "mean_control": float(mean_control),
        "mean_treatment": float(mean_treatment),
        "std_control": float(std_control),
        "std_treatment": float(std_treatment),
        "p_value": float(p_value),
        "effect_size": float(mean_treatment - mean_control),
    }


def generate_synthetic_dataset(
    total_records: int = TOTAL_RECORDS, seed: int = SEED
) -> List[Dict[str, Any]]:
    """
    Generate the full synthetic dataset.
    """
    set_all_seeds(seed)
    records = []
    binary_count = 0
    continuous_count = 0

    for i in range(total_records):
        # Determine outcome type
        is_binary = random.random() < BINARY_RATIO
        domain = random.choice(DOMAINS)
        year = random.choice(YEARS)
        n1, n2 = generate_sample_sizes(random.randint(MIN_SAMPLE_SIZE, MAX_SAMPLE_SIZE))

        record = {
            "id": f"synthetic_{i:05d}",
            "domain": domain,
            "year": year,
            "timestamp": datetime.now().isoformat(),
        }

        if is_binary:
            baseline = random.choice(BASELINE_RATES)
            effect = random.choice(EFFECT_SIZES) * random.choice([1, -1])
            data = generate_binary_outcome(baseline, effect, n1, n2)
            binary_count += 1
        else:
            baseline = random.uniform(10, 100)
            effect = random.uniform(-5, 5)
            data = generate_continuous_outcome(baseline, effect, n1, n2)
            continuous_count += 1

        record.update(data)
        records.append(record)

    logger.info(f"Generated {binary_count} binary and {continuous_count} continuous records")
    return records


def verify_outcome_types(records: List[Dict[str, Any]]) -> bool:
    """Verify that both binary and continuous outcomes are present."""
    has_binary = any(r["outcome_type"] == "binary" for r in records)
    has_continuous = any(r["outcome_type"] == "continuous" for r in records)
    if not has_binary:
        logger.error("Dataset missing binary outcomes")
    if not has_continuous:
        logger.error("Dataset missing continuous outcomes")
    return has_binary and has_continuous


def write_csv_output(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Write records to a CSV file."""
    if not records:
        logger.warning("No records to write")
        return

    fieldnames = list(records[0].keys())
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    logger.info(f"Wrote {len(records)} records to {output_path}")


def write_metadata(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Write metadata about the generated dataset."""
    metadata = {
        "total_records": len(records),
        "binary_count": sum(1 for r in records if r["outcome_type"] == "binary"),
        "continuous_count": sum(1 for r in records if r["outcome_type"] == "continuous"),
        "generated_at": datetime.now().isoformat(),
        "seed": SEED,
        "domains": list(set(r["domain"] for r in records)),
        "years": list(set(r["year"] for r in records)),
    }
    meta_path = output_path.with_suffix(".meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Wrote metadata to {meta_path}")


def main() -> None:
    """Main entry point for synthetic dataset generation."""
    logger.info("Starting synthetic dataset generation (Task T026)")

    output_dir = Path("data/synthetic")
    output_file = output_dir / "synthetic_summaries.csv"

    # Generate dataset
    records = generate_synthetic_dataset()

    # Verify constraints
    if not verify_outcome_types(records):
        logger.error("Failed to verify outcome types. Exiting.")
        return

    if len(records) < 10000:
        logger.error(f"Generated {len(records)} records, expected >= 10000")
        return

    # Write outputs
    write_csv_output(records, output_file)
    write_metadata(records, output_file)

    logger.info("Synthetic dataset generation completed successfully")


if __name__ == "__main__":
    main()
