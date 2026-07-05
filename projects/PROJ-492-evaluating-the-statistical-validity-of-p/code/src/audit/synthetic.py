"""
Synthetic Dataset Generator (FR-030)

Generates a synthetic corpus of A/B test summaries for validation purposes.
Outputs at least 10,000 records containing both binary and continuous outcomes.
Ensures deterministic behavior via seeded RNGs.
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
from scipy import stats

# Import from project API surface
from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.models.data_models import ABTestSummary

logger = get_default_logger(__name__)


def set_all_seeds(seed: int = SEED) -> None:
    """Seed all random number generators for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Seeded RNGs with seed={seed}")


def generate_sample_sizes(n_min: int = 50, n_max: int = 5000) -> Tuple[int, int]:
    """
    Generate realistic sample sizes for control and treatment groups.
    Uses a log-normal distribution to simulate realistic web traffic variance.
    """
    # Control group
    n_control = int(np.random.lognormal(mean=6.0, sigma=0.8))
    n_control = max(n_min, min(n_control, n_max))

    # Treatment group (often similar but can vary)
    n_treatment = int(np.random.lognormal(mean=6.0, sigma=0.8))
    n_treatment = max(n_min, min(n_treatment, n_max))

    return n_control, n_treatment


def generate_binary_outcome(
    n_control: int,
    n_treatment: int,
    baseline_rate: float,
    effect_size: float,
    is_inconsistent: bool = False
) -> Dict[str, Any]:
    """
    Generate binary outcome data (conversion rates).
    
    Args:
        n_control: Sample size for control group
        n_treatment: Sample size for treatment group
        baseline_rate: True conversion rate for control (0.01 to 0.20)
        effect_size: True relative lift (e.g., 0.10 for 10% lift)
        is_inconsistent: If True, report a p-value that contradicts the data
    
    Returns:
        Dictionary with metrics and reported statistics
    """
    # Generate actual successes
    p_control_true = baseline_rate
    p_treatment_true = baseline_rate * (1 + effect_size)
    
    successes_control = np.random.binomial(n_control, p_control_true)
    successes_treatment = np.random.binomial(n_treatment, p_treatment_true)
    
    # Calculate observed rates
    rate_control = successes_control / n_control
    rate_treatment = successes_treatment / n_treatment
    
    # Calculate true effect size (relative)
    if rate_control > 0:
        observed_lift = (rate_treatment - rate_control) / rate_control
    else:
        observed_lift = 0.0
    
    # Perform two-proportion z-test
    # Using scipy for accurate p-value calculation
    try:
        stat, p_value_true = stats.proportions_ztest(
            [successes_control, successes_treatment],
            [n_control, n_treatment]
        )
    except Exception:
        # Fallback for edge cases
        p_value_true = 1.0
        stat = 0.0
    
    # Determine reported p-value
    if is_inconsistent:
        # Flip the significance: if p < 0.05, report p > 0.05 and vice versa
        if p_value_true < 0.05:
            p_value_reported = round(random.uniform(0.06, 0.50), 4)
        else:
            p_value_reported = round(random.uniform(0.001, 0.04), 4)
    else:
        p_value_reported = round(p_value_true, 4)
    
    return {
        "successes_control": int(successes_control),
        "successes_treatment": int(successes_treatment),
        "n_control": int(n_control),
        "n_treatment": int(n_treatment),
        "rate_control": round(rate_control, 6),
        "rate_treatment": round(rate_treatment, 6),
        "reported_p_value": p_value_reported,
        "true_p_value": round(p_value_true, 6),
        "reported_lift": round(observed_lift, 4),
        "outcome_type": "binary"
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
    Generate continuous outcome data (e.g., revenue per user).
    
    Args:
        n_control: Sample size for control group
        n_treatment: Sample size for treatment group
        baseline_mean: True mean for control
        baseline_std: True standard deviation for control
        effect_size: True relative lift
        is_inconsistent: If True, report a p-value that contradicts the data
    
    Returns:
        Dictionary with metrics and reported statistics
    """
    # Generate actual data
    data_control = np.random.normal(baseline_mean, baseline_std, n_control)
    data_treatment = np.random.normal(
        baseline_mean * (1 + effect_size), 
        baseline_std, 
        n_treatment
    )
    
    # Calculate observed statistics
    mean_control = float(np.mean(data_control))
    mean_treatment = float(np.mean(data_treatment))
    std_control = float(np.std(data_control, ddof=1))
    std_treatment = float(np.std(data_treatment, ddof=1))
    
    # Calculate observed lift
    if mean_control > 0:
        observed_lift = (mean_treatment - mean_control) / mean_control
    else:
        observed_lift = 0.0
    
    # Perform Welch's t-test
    try:
        stat, p_value_true = stats.ttest_ind(
            data_control, data_treatment, equal_var=False
        )
    except Exception:
        p_value_true = 1.0
        stat = 0.0
    
    # Determine reported p-value
    if is_inconsistent:
        if p_value_true < 0.05:
            p_value_reported = round(random.uniform(0.06, 0.50), 4)
        else:
            p_value_reported = round(random.uniform(0.001, 0.04), 4)
    else:
        p_value_reported = round(p_value_true, 4)
    
    return {
        "mean_control": round(mean_control, 4),
        "mean_treatment": round(mean_treatment, 4),
        "std_control": round(std_control, 4),
        "std_treatment": round(std_treatment, 4),
        "n_control": int(n_control),
        "n_treatment": int(n_treatment),
        "reported_p_value": p_value_reported,
        "true_p_value": round(p_value_true, 6),
        "reported_lift": round(observed_lift, 4),
        "outcome_type": "continuous"
    }


def generate_synthetic_dataset(
    total_records: int = 10000,
    binary_ratio: float = 0.5,
    inconsistency_rate: float = 0.15,
    output_dir: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Generate a full synthetic dataset.
    
    Args:
        total_records: Total number of summaries to generate (min 10000)
        binary_ratio: Proportion of binary outcomes (default 0.5)
        inconsistency_rate: Proportion of summaries with inconsistent p-values
        output_dir: Directory to write output files (default: data/synthetic)
    
    Returns:
        List of generated summary dictionaries
    """
    if total_records < 10000:
        logger.warning(f"Requested {total_records} records; minimum is 10000. Using 10000.")
        total_records = 10000
    
    set_all_seeds()
    
    if output_dir is None:
        output_dir = Path("data/synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    summaries = []
    num_binary = int(total_records * binary_ratio)
    num_continuous = total_records - num_binary
    
    # Generate binary outcomes
    for i in range(num_binary):
        n_c, n_t = generate_sample_sizes()
        base_rate = random.uniform(0.01, 0.20)
        effect = random.choice([0.0, 0.05, 0.10, 0.15, -0.05, -0.10])
        is_inconsistent = random.random() < inconsistency_rate
        
        record = generate_binary_outcome(
            n_c, n_t, base_rate, effect, is_inconsistent
        )
        record["id"] = f"BINARY_{i:05d}"
        record["domain"] = random.choice([
            "ecommerce", "media", "finance", "health", "tech"
        ])
        record["year"] = random.randint(2020, 2024)
        summaries.append(record)
    
    # Generate continuous outcomes
    for i in range(num_continuous):
        n_c, n_t = generate_sample_sizes()
        base_mean = random.uniform(1.0, 100.0)
        base_std = base_mean * random.uniform(0.5, 2.0)
        effect = random.choice([0.0, 0.05, 0.10, 0.15, -0.05, -0.10])
        is_inconsistent = random.random() < inconsistency_rate
        
        record = generate_continuous_outcome(
            n_c, n_t, base_mean, base_std, effect, is_inconsistent
        )
        record["id"] = f"CONT_{i:05d}"
        record["domain"] = random.choice([
            "ecommerce", "media", "finance", "health", "tech"
        ])
        record["year"] = random.randint(2020, 2024)
        summaries.append(record)
    
    logger.info(f"Generated {len(summaries)} synthetic summaries")
    return summaries


def write_csv_output(summaries: List[Dict[str, Any]], filepath: Path) -> None:
    """Write summaries to CSV file."""
    if not summaries:
        logger.warning("No summaries to write to CSV.")
        return
    
    fieldnames = list(summaries[0].keys())
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)
    
    logger.info(f"Wrote {len(summaries)} records to {filepath}")


def write_json_output(summaries: List[Dict[str, Any]], filepath: Path) -> None:
    """Write summaries to JSON file."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2)
    
    logger.info(f"Wrote {len(summaries)} records to {filepath}")


def write_metadata(summaries: List[Dict[str, Any]], filepath: Path) -> None:
    """Write generation metadata."""
    binary_count = sum(1 for s in summaries if s["outcome_type"] == "binary")
    continuous_count = sum(1 for s in summaries if s["outcome_type"] == "continuous")
    inconsistent_count = sum(1 for s in summaries if s["reported_p_value"] != s["true_p_value"])
    
    metadata = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_records": len(summaries),
        "binary_outcomes": binary_count,
        "continuous_outcomes": continuous_count,
        "inconsistent_summaries": inconsistent_count,
        "seed": SEED,
        "version": "1.0.0"
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Wrote metadata to {filepath}")


def verify_outcome_types(summaries: List[Dict[str, Any]]) -> Tuple[int, int]:
    """
    Verify that both outcome types are present in the dataset.
    
    Returns:
        Tuple of (binary_count, continuous_count)
    """
    binary_count = sum(1 for s in summaries if s["outcome_type"] == "binary")
    continuous_count = sum(1 for s in summaries if s["outcome_type"] == "continuous")
    
    logger.info(f"Verification: Binary={binary_count}, Continuous={continuous_count}")
    
    if binary_count == 0:
        raise ValueError("No binary outcomes found in generated dataset.")
    if continuous_count == 0:
        raise ValueError("No continuous outcomes found in generated dataset.")
    
    return binary_count, continuous_count


def main() -> None:
    """Main entry point for synthetic dataset generation."""
    logger.info("Starting synthetic dataset generation...")
    
    output_dir = Path("data/synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate dataset
    summaries = generate_synthetic_dataset(
        total_records=10000,
        binary_ratio=0.5,
        inconsistency_rate=0.15
    )
    
    # Verify outcome types
    binary_count, continuous_count = verify_outcome_types(summaries)
    
    # Write outputs
    write_csv_output(summaries, output_dir / "synthetic_summaries.csv")
    write_json_output(summaries, output_dir / "synthetic_summaries.json")
    write_metadata(summaries, output_dir / "generation_metadata.json")
    
    logger.info(f"Synthetic dataset generation complete. "
                f"Total: {len(summaries)}, Binary: {binary_count}, "
                f"Continuous: {continuous_count}")


if __name__ == "__main__":
    main()
