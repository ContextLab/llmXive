"""
Synthetic dataset generator for A/B test audit validation (FR-030).

Generates at least 10,000 simulated A/B test summaries with both binary and continuous outcomes.
Outputs are written to data/synthetic/ directory in CSV and JSON formats.
"""
import csv
import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np

from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger

# Constants
MIN_RECORDS = 10000
BINARY_RATIO = 0.5  # 50% binary, 50% continuous
DOMAINS = ["ecommerce", "finance", "healthcare", "tech", "education"]
YEARS = list(range(2020, 2025))

logger = get_default_logger(__name__)


def set_all_seeds(seed: int = SEED) -> None:
    """Set all random seeds for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Seeds set to {seed}")


def generate_sample_sizes(min_n: int = 100, max_n: int = 50000) -> Tuple[int, int]:
    """Generate realistic sample sizes for control and treatment groups."""
    n_control = random.randint(min_n, max_n)
    # Treatment size typically within 10% of control
    n_treatment = int(n_control * random.uniform(0.9, 1.1))
    return n_control, n_treatment


def generate_binary_outcome(
    n_control: int,
    n_treatment: int,
    baseline_rate: float,
    effect_size: float,
    is_inconsistent: bool = False
) -> Dict[str, Any]:
    """
    Generate synthetic binary outcome A/B test data.

    Args:
        n_control: Sample size for control group
        n_treatment: Sample size for treatment group
        baseline_rate: Conversion rate for control group
        effect_size: True effect size (difference in rates)
        is_inconsistent: If True, generate reported p-value that mismatches data

    Returns:
        Dictionary with binary outcome metrics
    """
    # Generate true conversion counts
    control_conversions = int(n_control * baseline_rate)
    true_treatment_rate = baseline_rate + effect_size
    treatment_conversions = int(n_treatment * true_treatment_rate)

    # Clamp conversions to valid range
    control_conversions = max(0, min(n_control, control_conversions))
    treatment_conversions = max(0, min(n_treatment, treatment_conversions))

    # Calculate observed rates
    observed_control_rate = control_conversions / n_control
    observed_treatment_rate = treatment_conversions / n_treatment
    observed_effect = observed_treatment_rate - observed_control_rate

    # Calculate true p-value using two-proportion z-test
    pooled_rate = (control_conversions + treatment_conversions) / (n_control + n_treatment)
    if pooled_rate == 0 or pooled_rate == 1:
        true_p_value = 1.0
    else:
        se = np.sqrt(pooled_rate * (1 - pooled_rate) * (1/n_control + 1/n_treatment))
        z_stat = (observed_treatment_rate - observed_control_rate) / se if se > 0 else 0
        true_p_value = 2 * (1 - abs(stats.norm.cdf(abs(z_stat))))

    # Generate reported p-value (possibly inconsistent)
    if is_inconsistent:
        # Make reported p-value significantly different from true p-value
        reported_p_value = true_p_value * random.uniform(0.1, 0.5) if true_p_value > 0.01 else random.uniform(0.001, 0.04)
    else:
        # Add small noise to true p-value
        reported_p_value = true_p_value * random.uniform(0.95, 1.05)

    return {
        "outcome_type": "binary",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "control_conversions": control_conversions,
        "treatment_conversions": treatment_conversions,
        "baseline_rate": observed_control_rate,
        "treatment_rate": observed_treatment_rate,
        "effect_size": observed_effect,
        "true_p_value": true_p_value,
        "reported_p_value": reported_p_value,
        "is_inconsistent": is_inconsistent
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
    Generate synthetic continuous outcome A/B test data.

    Args:
        n_control: Sample size for control group
        n_treatment: Sample size for treatment group
        baseline_mean: Mean for control group
        baseline_std: Standard deviation for control group
        effect_size: True effect size (difference in means)
        is_inconsistent: If True, generate reported p-value that mismatches data

    Returns:
        Dictionary with continuous outcome metrics
    """
    # Generate observed statistics with some noise
    control_mean = baseline_mean + random.gauss(0, baseline_std / np.sqrt(n_control))
    treatment_mean = baseline_mean + effect_size + random.gauss(0, baseline_std / np.sqrt(n_treatment))

    # Generate standard deviations with some variation
    control_std = baseline_std * random.uniform(0.9, 1.1)
    treatment_std = baseline_std * random.uniform(0.9, 1.1)

    observed_effect = treatment_mean - control_mean

    # Calculate true p-value using Welch's t-test
    se = np.sqrt((control_std**2 / n_control) + (treatment_std**2 / n_treatment))
    t_stat = observed_effect / se if se > 0 else 0
    df = ((control_std**2 / n_control) + (treatment_std**2 / n_treatment))**2 / (
        (control_std**2 / n_control)**2 / (n_control - 1) +
        (treatment_std**2 / n_treatment)**2 / (n_treatment - 1)
    )
    true_p_value = 2 * (1 - abs(stats.t.cdf(abs(t_stat), df)))

    # Generate reported p-value
    if is_inconsistent:
        reported_p_value = true_p_value * random.uniform(0.1, 0.5) if true_p_value > 0.01 else random.uniform(0.001, 0.04)
    else:
        reported_p_value = true_p_value * random.uniform(0.95, 1.05)

    return {
        "outcome_type": "continuous",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "control_mean": control_mean,
        "treatment_mean": treatment_mean,
        "control_std": control_std,
        "treatment_std": treatment_std,
        "effect_size": observed_effect,
        "true_p_value": true_p_value,
        "reported_p_value": reported_p_value,
        "is_inconsistent": is_inconsistent
    }


def generate_synthetic_dataset(
    n_records: int = MIN_RECORDS,
    inconsistency_rate: float = 0.15
) -> List[Dict[str, Any]]:
    """
    Generate a synthetic dataset of A/B test summaries.

    Args:
        n_records: Number of records to generate (minimum 10,000)
        inconsistency_rate: Proportion of records with inconsistent p-values

    Returns:
        List of synthetic A/B test summary dictionaries
    """
    if n_records < MIN_RECORDS:
        logger.warning(f"Requested {n_records} records, using minimum {MIN_RECORDS}")
        n_records = MIN_RECORDS

    records = []
    n_binary = int(n_records * BINARY_RATIO)
    n_continuous = n_records - n_binary

    logger.info(f"Generating {n_binary} binary and {n_continuous} continuous records")

    # Generate binary outcomes
    for _ in range(n_binary):
        n_control, n_treatment = generate_sample_sizes()
        baseline_rate = random.uniform(0.01, 0.5)
        effect_size = random.choice([
            random.uniform(-0.05, -0.01),
            random.uniform(0.01, 0.05)
        ])
        is_inconsistent = random.random() < inconsistency_rate
        record = generate_binary_outcome(
            n_control, n_treatment, baseline_rate, effect_size, is_inconsistent
        )
        record["domain"] = random.choice(DOMAINS)
        record["year"] = random.choice(YEARS)
        record["id"] = f"synthetic_{len(records)+1}"
        records.append(record)

    # Generate continuous outcomes
    for _ in range(n_continuous):
        n_control, n_treatment = generate_sample_sizes()
        baseline_mean = random.uniform(10, 100)
        baseline_std = random.uniform(5, 20)
        effect_size = random.choice([
            random.uniform(-5, -1),
            random.uniform(1, 5)
        ])
        is_inconsistent = random.random() < inconsistency_rate
        record = generate_continuous_outcome(
            n_control, n_treatment, baseline_mean, baseline_std, effect_size, is_inconsistent
        )
        record["domain"] = random.choice(DOMAINS)
        record["year"] = random.choice(YEARS)
        record["id"] = f"synthetic_{len(records)+1}"
        records.append(record)

    logger.info(f"Generated {len(records)} synthetic records")
    return records


def verify_outcome_types(records: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Verify that both binary and continuous outcome types are present.

    Args:
        records: List of synthetic records

    Returns:
        Dictionary with counts of each outcome type

    Raises:
        ValueError: If either outcome type is missing
    """
    counts = {"binary": 0, "continuous": 0}
    for record in records:
        outcome_type = record.get("outcome_type")
        if outcome_type in counts:
            counts[outcome_type] += 1

    logger.info(f"Outcome type distribution: {counts}")

    if counts["binary"] == 0:
        raise ValueError("No binary outcomes generated")
    if counts["continuous"] == 0:
        raise ValueError("No continuous outcomes generated")

    return counts


def write_csv_output(records: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write synthetic records to CSV file.

    Args:
        records: List of synthetic records
        output_path: Path to output CSV file
    """
    if not records:
        raise ValueError("No records to write")

    # Define columns in a consistent order
    columns = [
        "id", "outcome_type", "domain", "year",
        "n_control", "n_treatment",
        "baseline_rate", "treatment_rate",  # For binary
        "control_mean", "treatment_mean", "control_std", "treatment_std",  # For continuous
        "control_conversions", "treatment_conversions",  # For binary
        "effect_size", "true_p_value", "reported_p_value", "is_inconsistent"
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(records)

    logger.info(f"Wrote {len(records)} records to {output_path}")


def write_json_output(records: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write synthetic records to JSON file.

    Args:
        records: List of synthetic records
        output_path: Path to output JSON file
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2)

    logger.info(f"Wrote {len(records)} records to {output_path}")


def write_metadata(output_dir: Path, records: List[Dict[str, Any]], outcome_counts: Dict[str, int]) -> None:
    """
    Write metadata about the synthetic dataset.

    Args:
        output_dir: Directory for output files
        records: List of synthetic records
        outcome_counts: Dictionary with outcome type counts
    """
    metadata = {
        "generated_at": datetime.now().isoformat(),
        "total_records": len(records),
        "outcome_type_counts": outcome_counts,
        "inconsistency_rate": sum(1 for r in records if r.get("is_inconsistent")) / len(records),
        "domains": list(set(r["domain"] for r in records)),
        "years": list(set(r["year"] for r in records)),
        "seed": SEED
    }

    metadata_path = output_dir / "synthetic_metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Wrote metadata to {metadata_path}")


def main() -> None:
    """Main entry point for synthetic dataset generation."""
    # Set seeds for reproducibility
    set_all_seeds()

    # Ensure output directory exists
    output_dir = Path("data/synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate dataset
    records = generate_synthetic_dataset(n_records=MIN_RECORDS)

    # Verify outcome types
    outcome_counts = verify_outcome_types(records)

    # Write outputs
    csv_path = output_dir / "synthetic_summaries.csv"
    json_path = output_dir / "synthetic_summaries.json"

    write_csv_output(records, csv_path)
    write_json_output(records, json_path)
    write_metadata(output_dir, records, outcome_counts)

    # Final verification
    assert len(records) >= MIN_RECORDS, f"Generated {len(records)} records, expected >= {MIN_RECORDS}"
    assert outcome_counts["binary"] > 0, "No binary outcomes generated"
    assert outcome_counts["continuous"] > 0, "No continuous outcomes generated"

    logger.info(f"Synthetic dataset generation complete: {len(records)} records")
    logger.info(f"Binary: {outcome_counts['binary']}, Continuous: {outcome_counts['continuous']}")


if __name__ == "__main__":
    main()
