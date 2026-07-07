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
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
from scipy import stats

from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.models.data_models import ABTestSummary

logger = get_default_logger(__name__)

# Constants for synthetic data generation
MIN_SAMPLE_SIZE = 50
MAX_SAMPLE_SIZE = 5000
BASELINE_RANGE = (0.05, 0.50)
EFFECT_SIZE_RANGE = (-0.10, 0.10)
CONTINUOUS_MEAN_BASELINE = 100.0
CONTINUOUS_STD_BASELINE = 15.0
CONTINUOUS_EFFECT_RANGE = (-5.0, 5.0)
DOMAINS = ["tech", "finance", "health", "e-commerce", "education"]
YEARS = list(range(2018, 2025))

def set_all_seeds(seed: int = SEED) -> None:
    """Set random seeds for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Random seeds set to {seed}")

def generate_sample_sizes(n: int) -> List[int]:
    """Generate n sample sizes uniformly distributed."""
    return [random.randint(MIN_SAMPLE_SIZE, MAX_SAMPLE_SIZE) for _ in range(n)]

def generate_binary_outcome(
    n: int,
    baseline_rate: float,
    effect_size: float,
    seed: Optional[int] = None
) -> Tuple[int, int, int, int, float]:
    """
    Generate binary outcome A/B test data.

    Returns:
        (n_control, n_treatment, successes_control, successes_treatment, p_value)
    """
    if seed is not None:
        np.random.seed(seed)

    n_control = n
    n_treatment = n

    # Apply effect size to baseline
    treatment_rate = baseline_rate + effect_size
    treatment_rate = max(0.0, min(1.0, treatment_rate))  # Clamp to [0, 1]

    # Generate successes
    successes_control = np.random.binomial(n_control, baseline_rate)
    successes_treatment = np.random.binomial(n_treatment, treatment_rate)

    # Perform two-proportion z-test
    # Using scipy.stats.proportions_ztest
    try:
        count = np.array([successes_control, successes_treatment])
        nobs = np.array([n_control, n_treatment])
        z_stat, p_value = stats.proportions_ztest(count, nobs)
    except Exception as e:
        logger.warning(f"Z-test failed: {e}, using fallback p-value")
        p_value = 0.5

    return n_control, n_treatment, successes_control, successes_treatment, p_value

def generate_continuous_outcome(
    n: int,
    effect_size: float,
    seed: Optional[int] = None
) -> Tuple[int, int, float, float, float, float, float]:
    """
    Generate continuous outcome A/B test data.

    Returns:
        (n_control, n_treatment, mean_control, mean_treatment,
         std_control, std_treatment, p_value)
    """
    if seed is not None:
        np.random.seed(seed)

    n_control = n
    n_treatment = n

    # Generate data
    data_control = np.random.normal(CONTINUOUS_MEAN_BASELINE, CONTINUOUS_STD_BASELINE, n_control)
    data_treatment = np.random.normal(
        CONTINUOUS_MEAN_BASELINE + effect_size,
        CONTINUOUS_STD_BASELINE,
        n_treatment
    )

    mean_control = float(np.mean(data_control))
    mean_treatment = float(np.mean(data_treatment))
    std_control = float(np.std(data_control, ddof=1))
    std_treatment = float(np.std(data_treatment, ddof=1))

    # Perform Welch's t-test
    try:
        t_stat, p_value = stats.ttest_ind(
            data_control, data_treatment, equal_var=False
        )
    except Exception as e:
        logger.warning(f"T-test failed: {e}, using fallback p-value")
        p_value = 0.5

    return n_control, n_treatment, mean_control, mean_treatment, std_control, std_treatment, p_value

def generate_synthetic_dataset(
    total_records: int = 10000,
    binary_ratio: float = 0.5,
    output_dir: Path = Path("data/generated"),
    seed: int = SEED
) -> Dict[str, Any]:
    """
    Generate a synthetic dataset of A/B test summaries.

    Args:
        total_records: Total number of records to generate (>= 10000)
        binary_ratio: Ratio of binary outcomes (0.5 = 50% binary, 50% continuous)
        output_dir: Directory to write output files
        seed: Random seed for reproducibility

    Returns:
        Metadata dictionary about the generated dataset
    """
    if total_records < 10000:
        raise ValueError(f"total_records must be >= 10000, got {total_records}")

    set_all_seeds(seed)
    output_dir.mkdir(parents=True, exist_ok=True)

    num_binary = int(total_records * binary_ratio)
    num_continuous = total_records - num_binary

    logger.info(f"Generating {num_binary} binary and {num_continuous} continuous records")

    records = []
    record_id = 1

    # Generate binary outcomes
    for i in range(num_binary):
        n = random.randint(MIN_SAMPLE_SIZE, MAX_SAMPLE_SIZE)
        baseline = random.uniform(*BASELINE_RANGE)
        effect = random.uniform(*EFFECT_SIZE_RANGE)
        domain = random.choice(DOMAINS)
        year = random.choice(YEARS)

        n_control, n_treatment, succ_c, succ_t, p_val = generate_binary_outcome(
            n, baseline, effect
        )

        effect_size = (succ_t / n_treatment) - (succ_c / n_control)

        record = {
            "id": record_id,
            "outcome_type": "binary",
            "domain": domain,
            "year": year,
            "n_control": n_control,
            "n_treatment": n_treatment,
            "successes_control": succ_c,
            "successes_treatment": succ_t,
            "baseline_rate": baseline,
            "treatment_rate": succ_t / n_treatment if n_treatment > 0 else 0.0,
            "effect_size": effect_size,
            "p_value": p_val,
            "significant": p_val < 0.05,
            "url": f"https://example.com/test/{record_id}",
            "title": f"Test {record_id}: {domain} experiment",
        }
        records.append(record)
        record_id += 1

    # Generate continuous outcomes
    for i in range(num_continuous):
        n = random.randint(MIN_SAMPLE_SIZE, MAX_SAMPLE_SIZE)
        effect = random.uniform(*CONTINUOUS_EFFECT_RANGE)
        domain = random.choice(DOMAINS)
        year = random.choice(YEARS)

        (n_control, n_treatment, mean_c, mean_t, std_c, std_t, p_val) = (
            generate_continuous_outcome(n, effect)
        )

        effect_size = mean_t - mean_c

        record = {
            "id": record_id,
            "outcome_type": "continuous",
            "domain": domain,
            "year": year,
            "n_control": n_control,
            "n_treatment": n_treatment,
            "mean_control": mean_c,
            "mean_treatment": mean_t,
            "std_control": std_c,
            "std_treatment": std_t,
            "effect_size": effect_size,
            "p_value": p_val,
            "significant": p_val < 0.05,
            "url": f"https://example.com/test/{record_id}",
            "title": f"Test {record_id}: {domain} continuous experiment",
        }
        records.append(record)
        record_id += 1

    # Write CSV output
    csv_path = output_dir / "synthetic_summaries.csv"
    write_csv_output(records, csv_path)

    # Write metadata
    metadata = {
        "total_records": len(records),
        "binary_count": num_binary,
        "continuous_count": num_continuous,
        "domains": DOMAINS,
        "years": YEARS,
        "generation_timestamp": datetime.now().isoformat(),
        "seed": seed,
        "output_file": str(csv_path),
    }
    metadata_path = output_dir / "synthetic_metadata.json"
    write_metadata(metadata, metadata_path)

    # Verify outcome types
    verify_outcome_types(records, num_binary, num_continuous)

    logger.info(f"Successfully generated {len(records)} synthetic records")
    return metadata

def verify_outcome_types(
    records: List[Dict[str, Any]],
    expected_binary: int,
    expected_continuous: int
) -> None:
    """Verify that the generated dataset contains the expected number of each outcome type."""
    binary_count = sum(1 for r in records if r["outcome_type"] == "binary")
    continuous_count = sum(1 for r in records if r["outcome_type"] == "continuous")

    if binary_count != expected_binary:
        raise ValueError(
            f"Binary count mismatch: expected {expected_binary}, got {binary_count}"
        )
    if continuous_count != expected_continuous:
        raise ValueError(
            f"Continuous count mismatch: expected {expected_continuous}, got {continuous_count}"
        )
    if binary_count == 0 or continuous_count == 0:
        raise ValueError(
            "Both binary and continuous outcomes must be present in the dataset"
        )

    logger.info(
        f"Verification passed: {binary_count} binary, {continuous_count} continuous"
    )

def write_csv_output(records: List[Dict[str, Any]], path: Path) -> None:
    """Write records to a CSV file."""
    if not records:
        raise ValueError("No records to write")

    fieldnames = list(records[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    logger.info(f"Wrote {len(records)} records to {path}")

def write_metadata(metadata: Dict[str, Any], path: Path) -> None:
    """Write metadata to a JSON file."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Wrote metadata to {path}")

def main() -> int:
    """Main entry point for synthetic dataset generation."""
    try:
        output_dir = Path("data/generated")
        metadata = generate_synthetic_dataset(
            total_records=10000,
            binary_ratio=0.5,
            output_dir=output_dir,
            seed=SEED
        )
        print(f"Generated {metadata['total_records']} records")
        print(f"Binary: {metadata['binary_count']}, Continuous: {metadata['continuous_count']}")
        return 0
    except Exception as e:
        logger.error(f"Failed to generate synthetic dataset: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
