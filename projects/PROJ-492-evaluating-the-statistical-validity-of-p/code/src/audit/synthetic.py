"""
Synthetic Dataset Generator (FR-030)

Generates a large corpus of simulated A/B test summaries for validation purposes.
Produces both binary and continuous outcome types with realistic statistical properties.
Outputs at least 10,000 records to data/synthetic/summaries.csv.
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
audit_logger = AuditLogger(logger)

# Constants for synthetic generation
TOTAL_RECORDS = 10000
BINARY_RATIO = 0.5  # 50% binary, 50% continuous
MIN_SAMPLE_SIZE = 50
MAX_SAMPLE_SIZE = 50000
BASELINE_RANGE = (0.01, 0.50)
EFFECT_SIZE_RANGE = (0.0, 0.20)  # Relative effect size
ALPHA = 0.05

def set_all_seeds(seed: int = SEED) -> None:
    """Set random seeds for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Seeds initialized with value {seed}")

def generate_sample_sizes(n: int = 1) -> Tuple[int, int]:
    """
    Generate realistic sample sizes for control and treatment groups.
    Uses a log-uniform distribution to mimic real-world variance.
    """
    # Control group size
    n_control = int(np.random.lognormal(mean=np.log(1000), sigma=1.0))
    n_control = max(MIN_SAMPLE_SIZE, min(n_control, MAX_SAMPLE_SIZE))

    # Treatment group size (usually similar to control, with some variance)
    ratio = np.random.beta(2, 2) * 0.4 + 0.8  # 0.8 to 1.2
    n_treatment = int(n_control * ratio)
    n_treatment = max(MIN_SAMPLE_SIZE, min(n_treatment, MAX_SAMPLE_SIZE))

    return n_control, n_treatment

def generate_binary_outcome(
    n_control: int, n_treatment: int, baseline_rate: float, effect_size: float, inject_inconsistency: bool = False
) -> Dict[str, Any]:
    """
    Generate binary outcome data (conversion rates).
    Returns counts and reported metrics.
    """
    # True rates
    p_control = baseline_rate
    p_treatment = baseline_rate * (1 + effect_size)
    p_treatment = min(max(p_treatment, 0.0), 1.0)

    # Generate actual successes
    x_control = np.random.binomial(n_control, p_control)
    x_treatment = np.random.binomial(n_treatment, p_treatment)

    # Observed rates
    rate_control = x_control / n_control
    rate_treatment = x_treatment / n_treatment

    # Calculate true p-value (two-proportion z-test)
    # Using pooled proportion for standard error
    p_pooled = (x_control + x_treatment) / (n_control + n_treatment)
    if p_pooled == 0 or p_pooled == 1:
        true_p_value = 1.0
    else:
        se = np.sqrt(p_pooled * (1 - p_pooled) * (1/n_control + 1/n_treatment))
        if se == 0:
            true_p_value = 1.0
        else:
            z_stat = (rate_treatment - rate_control) / se
            true_p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))

    # Reported metrics
    reported_p_value = true_p_value
    reported_effect_size = (rate_treatment - rate_control) / rate_control if rate_control > 0 else 0.0

    if inject_inconsistency:
        # Inject a small inconsistency (e.g., swap p-value slightly or report wrong effect)
        # Here we slightly alter the reported p-value to create a mismatch > 0.05 occasionally
        if np.random.rand() > 0.5:
            reported_p_value = min(1.0, true_p_value + 0.06)
        else:
            reported_effect_size = (rate_treatment - rate_control) / rate_control if rate_control > 0 else 0.0
            reported_effect_size += np.random.choice([-1, 1]) * 0.06

    return {
        "outcome_type": "binary",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "x_control": int(x_control),
        "x_treatment": int(x_treatment),
        "rate_control": float(rate_control),
        "rate_treatment": float(rate_treatment),
        "true_p_value": float(true_p_value),
        "reported_p_value": float(reported_p_value),
        "true_effect_size": float(effect_size),
        "reported_effect_size": float(reported_effect_size),
        "is_inconsistent": abs(reported_p_value - true_p_value) > 0.05
    }

def generate_continuous_outcome(
    n_control: int, n_treatment: int, baseline_mean: float, effect_size: float, inject_inconsistency: bool = False
) -> Dict[str, Any]:
    """
    Generate continuous outcome data (e.g., time on site, revenue).
    Returns means, stds, and reported metrics.
    """
    # True parameters
    mu_control = baseline_mean
    sigma_control = baseline_mean * 0.5  # Coefficient of variation ~0.5
    mu_treatment = baseline_mean * (1 + effect_size)
    sigma_treatment = sigma_control * (1 + effect_size * 0.1)  # Slight variance increase

    # Generate samples
    sample_control = np.random.normal(mu_control, sigma_control, n_control)
    sample_treatment = np.random.normal(mu_treatment, sigma_treatment, n_treatment)

    # Observed stats
    mean_control = float(np.mean(sample_control))
    mean_treatment = float(np.mean(sample_treatment))
    std_control = float(np.std(sample_control, ddof=1))
    std_treatment = float(np.std(sample_treatment, ddof=1))

    # True p-value (Welch's t-test)
    _, true_p_value = stats.ttest_ind(
        sample_control, sample_treatment, equal_var=False
    )

    # Effect size (Cohen's d)
    pooled_std = np.sqrt((std_control**2 + std_treatment**2) / 2)
    true_effect_size = (mean_treatment - mean_control) / pooled_std if pooled_std > 0 else 0.0

    # Reported metrics
    reported_p_value = true_p_value
    reported_effect_size = true_effect_size

    if inject_inconsistency:
        if np.random.rand() > 0.5:
            reported_p_value = min(1.0, true_p_value + 0.06)
        else:
            reported_effect_size = true_effect_size + np.random.choice([-1, 1]) * 0.15

    return {
        "outcome_type": "continuous",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "mean_control": float(mean_control),
        "mean_treatment": float(mean_treatment),
        "std_control": float(std_control),
        "std_treatment": float(std_treatment),
        "true_p_value": float(true_p_value),
        "reported_p_value": float(reported_p_value),
        "true_effect_size": float(true_effect_size),
        "reported_effect_size": float(reported_effect_size),
        "is_inconsistent": abs(reported_p_value - true_p_value) > 0.05
    }

def generate_synthetic_dataset(
    total_records: int = TOTAL_RECORDS,
    output_dir: Optional[Path] = None,
    seed: int = SEED
) -> List[Dict[str, Any]]:
    """
    Generate the full synthetic dataset.
    Returns list of dictionaries representing ABTestSummary-compatible records.
    """
    set_all_seeds(seed)

    if output_dir is None:
        output_dir = Path("code/data/synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Generating {total_records} synthetic summaries...")

    records = []
    binary_count = 0
    continuous_count = 0

    for i in range(total_records):
        # Randomize outcome type
        is_binary = np.random.rand() < BINARY_RATIO
        
        # Randomize parameters
        baseline = np.random.uniform(*BASELINE_RANGE)
        effect = np.random.uniform(*EFFECT_SIZE_RANGE)
        n_ctrl, n_trt = generate_sample_sizes()
        
        # 10% chance of inconsistency injection
        inject_inconsistency = np.random.rand() < 0.10

        if is_binary:
            data = generate_binary_outcome(
                n_ctrl, n_trt, baseline, effect, inject_inconsistency
            )
            binary_count += 1
        else:
            data = generate_continuous_outcome(
                n_ctrl, n_trt, baseline * 100, effect, inject_inconsistency
            ) # Scale baseline for continuous
            continuous_count += 1

        # Construct ABTestSummary-like record
        record = {
            "id": f"synth_{i:06d}",
            "url": f"https://example.com/test/{i}",
            "domain": "example.com",
            "year": np.random.randint(2020, 2025),
            "outcome_type": data["outcome_type"],
            "n_control": data["n_control"],
            "n_treatment": data["n_treatment"],
            "baseline_rate": data.get("rate_control", 0.0),
            "treatment_rate": data.get("rate_treatment", 0.0),
            "mean_control": data.get("mean_control", 0.0),
            "mean_treatment": data.get("mean_treatment", 0.0),
            "std_control": data.get("std_control", 0.0),
            "std_treatment": data.get("std_treatment", 0.0),
            "reported_p_value": data["reported_p_value"],
            "reported_effect_size": data["reported_effect_size"],
            "true_p_value": data["true_p_value"],
            "true_effect_size": data["true_effect_size"],
            "is_inconsistent": data["is_inconsistent"],
            "generated_at": datetime.utcnow().isoformat()
        }
        records.append(record)

    # Write to CSV
    csv_path = output_dir / "summaries.csv"
    if records:
        fieldnames = list(records[0].keys())
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)

    logger.info(f"Written {len(records)} records to {csv_path}")
    logger.info(f"Binary outcomes: {binary_count}, Continuous outcomes: {continuous_count}")

    # Write metadata
    metadata = {
        "total_records": len(records),
        "binary_count": binary_count,
        "continuous_count": continuous_count,
        "inconsistent_count": sum(1 for r in records if r["is_inconsistent"]),
        "seed": seed,
        "generated_at": datetime.utcnow().isoformat(),
        "output_path": str(csv_path)
    }
    metadata_path = output_dir / "metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Written metadata to {metadata_path}")

    return records

def verify_outcome_types(records: List[Dict[str, Any]], min_count: int = 1) -> bool:
    """
    Verify that both binary and continuous outcomes are present.
    """
    types = set(r["outcome_type"] for r in records)
    has_binary = "binary" in types
    has_continuous = "continuous" in types
    
    if not has_binary:
        audit_logger.error("ERR-SYNTH-001: No binary outcomes generated.")
        return False
    if not has_continuous:
        audit_logger.error("ERR-SYNTH-002: No continuous outcomes generated.")
        return False
    
    logger.info("Verification passed: Both binary and continuous outcomes present.")
    return True

def write_summaries(records: List[Dict[str, Any]], path: Path) -> None:
    """Helper to write summaries to CSV."""
    if not records:
        return
    fieldnames = list(records[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

def write_metadata(metadata: Dict[str, Any], path: Path) -> None:
    """Helper to write metadata to JSON."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

def main() -> int:
    """Main entry point for synthetic data generation."""
    try:
        output_dir = Path("code/data/synthetic")
        records = generate_synthetic_dataset(
            total_records=TOTAL_RECORDS,
            output_dir=output_dir,
            seed=SEED
        )
        
        if not verify_outcome_types(records):
            audit_logger.error("ERR-SYNTH-999: Outcome type verification failed.")
            return 1
        
        if len(records) < 10000:
            audit_logger.error(f"ERR-SYNTH-998: Generated {len(records)} records, expected >= 10000.")
            return 1

        logger.info("Synthetic dataset generation completed successfully.")
        return 0
    except Exception as e:
        audit_logger.critical(f"ERR-SYNTH-997: Fatal error during generation: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
