"""
Synthetic dataset generator for A/B test audit validation (FR-030).
Generates at least 10,000 simulated summaries with both binary and continuous outcomes.
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

# Constants for generation
MIN_SAMPLE_SIZE = 100
MAX_SAMPLE_SIZE = 100000
BINARY_BASELINE_MIN = 0.01
BINARY_BASELINE_MAX = 0.50
EFFECT_SIZE_MIN = 0.001
EFFECT_SIZE_MAX = 0.15
CONTINUOUS_MEAN_MIN = 0.0
CONTINUOUS_MEAN_MAX = 100.0
CONTINUOUS_STD_MIN = 5.0
CONTINUOUS_STD_MAX = 20.0
DOMAINS = ["tech", "finance", "health", "retail", "education"]
YEARS = list(range(2018, 2025))

def set_all_seeds(seed: int = SEED) -> None:
    """Set random seeds for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Seeds set to {seed}")

def generate_sample_sizes(n: int = 2) -> Tuple[int, int]:
    """Generate two sample sizes for control and treatment groups."""
    base_size = np.random.randint(MIN_SAMPLE_SIZE, MAX_SAMPLE_SIZE)
    # Allow some variation between groups (up to 20%)
    variation = np.random.uniform(0.8, 1.2)
    n_treatment = int(base_size * variation)
    return base_size, n_treatment

def generate_binary_outcome(n_control: int, n_treatment: int, baseline_rate: float, effect_size: float) -> Dict[str, float]:
    """
    Generate binary outcome data (success counts).
    Returns observed rates and p-value from z-test.
    """
    # Control success rate
    p_control = baseline_rate
    # Treatment success rate with effect
    p_treatment = baseline_rate + effect_size
    # Ensure rates are within [0, 1]
    p_treatment = max(0.0, min(1.0, p_treatment))

    # Generate observed successes
    successes_control = np.random.binomial(n_control, p_control)
    successes_treatment = np.random.binomial(n_treatment, p_treatment)

    # Calculate observed rates
    rate_control = successes_control / n_control
    rate_treatment = successes_treatment / n_treatment

    # Two-proportion z-test
    try:
        stat, p_value = stats.proportions_ztest(
            [successes_control, successes_treatment],
            [n_control, n_treatment]
        )
    except Exception as e:
        logger.warning(f"Z-test failed: {e}, using fallback")
        p_value = 1.0

    return {
        "n_control": n_control,
        "n_treatment": n_treatment,
        "successes_control": int(successes_control),
        "successes_treatment": int(successes_treatment),
        "rate_control": rate_control,
        "rate_treatment": rate_treatment,
        "p_value": p_value,
        "effect_size": p_treatment - p_control,
        "outcome_type": "binary"
    }

def generate_continuous_outcome(n_control: int, n_treatment: int, mean_control: float, effect_size: float, std_dev: float) -> Dict[str, float]:
    """
    Generate continuous outcome data.
    Returns means, std devs, and p-value from Welch's t-test.
    """
    # Generate data
    data_control = np.random.normal(mean_control, std_dev, n_control)
    data_treatment = np.random.normal(mean_control + effect_size, std_dev, n_treatment)

    # Calculate statistics
    mean_control_obs = float(np.mean(data_control))
    mean_treatment_obs = float(np.mean(data_treatment))
    std_control_obs = float(np.std(data_control, ddof=1))
    std_treatment_obs = float(np.std(data_treatment, ddof=1))

    # Welch's t-test
    try:
        stat, p_value = stats.ttest_ind(data_control, data_treatment, equal_var=False)
    except Exception as e:
        logger.warning(f"T-test failed: {e}, using fallback")
        p_value = 1.0

    return {
        "n_control": n_control,
        "n_treatment": n_treatment,
        "mean_control": mean_control_obs,
        "mean_treatment": mean_treatment_obs,
        "std_control": std_control_obs,
        "std_treatment": std_treatment_obs,
        "p_value": p_value,
        "effect_size": effect_size,
        "outcome_type": "continuous"
    }

def generate_synthetic_dataset(
    n_records: int = 10000,
    binary_ratio: float = 0.5,
    output_dir: Optional[Path] = None
) -> Tuple[List[Dict[str, Any]], int, int]:
    """
    Generate a synthetic dataset of A/B test summaries.
    
    Args:
        n_records: Total number of records to generate (minimum 10000)
        binary_ratio: Proportion of binary outcomes (default 0.5)
        output_dir: Directory to write output files (default: data/synthetic/)
    
    Returns:
        Tuple of (list of records, binary_count, continuous_count)
    """
    if output_dir is None:
        output_dir = Path("data/synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Ensure minimum count
    n_records = max(n_records, 10000)
    n_binary = int(n_records * binary_ratio)
    n_continuous = n_records - n_binary

    records = []
    binary_count = 0
    continuous_count = 0

    for i in range(n_records):
        # Determine outcome type
        is_binary = i < n_binary
        domain = random.choice(DOMAINS)
        year = random.choice(YEARS)

        # Generate sample sizes
        n_control, n_treatment = generate_sample_sizes()

        if is_binary:
            # Generate binary outcome
            baseline_rate = np.random.uniform(BINARY_BASELINE_MIN, BINARY_BASELINE_MAX)
            effect_size = np.random.uniform(EFFECT_SIZE_MIN, EFFECT_SIZE_MAX)
            # 20% chance of negative effect
            if random.random() < 0.2:
                effect_size = -effect_size

            result = generate_binary_outcome(n_control, n_treatment, baseline_rate, effect_size)
            binary_count += 1

            # Create summary record
            record = {
                "id": f"synthetic_{i:06d}",
                "url": f"https://example.com/{domain}/test_{i}",
                "domain": domain,
                "year": year,
                "outcome_type": "binary",
                "n_control": result["n_control"],
                "n_treatment": result["n_treatment"],
                "baseline_rate": result["rate_control"],
                "treatment_rate": result["rate_treatment"],
                "p_value": result["p_value"],
                "effect_size": result["effect_size"],
                "successes_control": result["successes_control"],
                "successes_treatment": result["successes_treatment"],
                "is_significant": result["p_value"] < 0.05
            }
        else:
            # Generate continuous outcome
            mean_control = np.random.uniform(CONTINUOUS_MEAN_MIN, CONTINUOUS_MEAN_MAX)
            std_dev = np.random.uniform(CONTINUOUS_STD_MIN, CONTINUOUS_STD_MAX)
            effect_size = np.random.uniform(EFFECT_SIZE_MIN * mean_control, EFFECT_SIZE_MAX * mean_control)
            # 20% chance of negative effect
            if random.random() < 0.2:
                effect_size = -effect_size

            result = generate_continuous_outcome(n_control, n_treatment, mean_control, effect_size, std_dev)
            continuous_count += 1

            # Create summary record
            record = {
                "id": f"synthetic_{i:06d}",
                "url": f"https://example.com/{domain}/test_{i}",
                "domain": domain,
                "year": year,
                "outcome_type": "continuous",
                "n_control": result["n_control"],
                "n_treatment": result["n_treatment"],
                "mean_control": result["mean_control"],
                "mean_treatment": result["mean_treatment"],
                "std_control": result["std_control"],
                "std_treatment": result["std_treatment"],
                "p_value": result["p_value"],
                "effect_size": result["effect_size"],
                "is_significant": result["p_value"] < 0.05
            }

        records.append(record)

    return records, binary_count, continuous_count

def verify_outcome_types(records: List[Dict[str, Any]], min_binary: int = 1000, min_continuous: int = 1000) -> bool:
    """
    Verify that both outcome types are present in sufficient quantities.
    
    Args:
        records: List of generated records
        min_binary: Minimum required binary records
        min_continuous: Minimum required continuous records
    
    Returns:
        True if verification passes, False otherwise
    """
    binary_count = sum(1 for r in records if r.get("outcome_type") == "binary")
    continuous_count = sum(1 for r in records if r.get("outcome_type") == "continuous")

    logger.info(f"Verification: Binary={binary_count}, Continuous={continuous_count}")

    if binary_count < min_binary:
        logger.error(f"Insufficient binary records: {binary_count} < {min_binary}")
        return False
    if continuous_count < min_continuous:
        logger.error(f"Insufficient continuous records: {continuous_count} < {min_continuous}")
        return False
    if len(records) < 10000:
        logger.error(f"Total records insufficient: {len(records)} < 10000")
        return False

    logger.info("Outcome type verification passed")
    return True

def write_csv_output(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Write records to CSV file."""
    if not records:
        logger.error("No records to write")
        return

    fieldnames = list(records[0].keys())
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    logger.info(f"Wrote {len(records)} records to {output_path}")

def write_json_output(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Write records to JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    logger.info(f"Wrote {len(records)} records to {output_path}")

def write_metadata(
    binary_count: int,
    continuous_count: int,
    total_count: int,
    output_path: Path
) -> None:
    """Write metadata about the generated dataset."""
    metadata = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_records": total_count,
        "binary_count": binary_count,
        "continuous_count": continuous_count,
        "binary_ratio": binary_count / total_count if total_count > 0 else 0,
        "version": "1.0",
        "seed": SEED
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Wrote metadata to {output_path}")

def main() -> int:
    """Main entry point for synthetic dataset generation."""
    try:
        logger.info("Starting synthetic dataset generation (T026)")
        set_all_seeds(SEED)

        # Generate dataset
        records, binary_count, continuous_count = generate_synthetic_dataset(
            n_records=10000,
            binary_ratio=0.5
        )

        # Verify outcome types
        if not verify_outcome_types(records):
            logger.error("Outcome type verification failed")
            return 1

        # Define output paths
        output_dir = Path("data/synthetic")
        output_dir.mkdir(parents=True, exist_ok=True)

        csv_path = output_dir / "synthetic_summaries.csv"
        json_path = output_dir / "synthetic_summaries.json"
        metadata_path = output_dir / "synthetic_metadata.json"

        # Write outputs
        write_csv_output(records, csv_path)
        write_json_output(records, json_path)
        write_metadata(binary_count, continuous_count, len(records), metadata_path)

        logger.info(f"Successfully generated {len(records)} synthetic records")
        logger.info(f"Binary: {binary_count}, Continuous: {continuous_count}")
        logger.info(f"Output files: {csv_path}, {json_path}, {metadata_path}")

        return 0

    except Exception as e:
        logger.error(f"Synthetic dataset generation failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
