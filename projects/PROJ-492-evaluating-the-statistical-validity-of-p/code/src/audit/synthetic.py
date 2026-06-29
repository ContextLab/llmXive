"""
Synthetic dataset generator for A/B test validation (FR-030).

Generates synthetic A/B test summaries with known ground truth for
validating the statistical consistency audit pipeline.

Outputs:
  - data/synthetic/synthetic_validation.csv: CSV with all synthetic summaries
  - data/synthetic/synthetic_ground_truth.json: JSON with metadata and consistency flags
"""
import csv
import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from scipy import stats

# Import from existing project modules
from code.src.models.data_models import ABTestSummary
from code.src.config import set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.utils.helpers import safe_float

# Constants
DEFAULT_SEED = 42
NUM_BINARY_OUTCOMES = 5000
NUM_CONTINUOUS_OUTCOMES = 5000
MIN_SAMPLE_SIZE = 100
MAX_SAMPLE_SIZE = 100000
MIN_BASELINE_RATE = 0.01
MAX_BASELINE_RATE = 0.50
MIN_EFFECT_SIZE = 0.001
MAX_EFFECT_SIZE = 0.50
CONSISTENT_FRACTION = 0.85  # 85% consistent, 15% inconsistent

# Output paths
OUTPUT_DIR = Path("data/synthetic")
CSV_OUTPUT = OUTPUT_DIR / "synthetic_validation.csv"
JSON_OUTPUT = OUTPUT_DIR / "synthetic_ground_truth.json"

logger = get_default_logger()

def set_all_seeds(seed: int = DEFAULT_SEED) -> None:
    """Set seeds for all random number generators."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)

def generate_binary_outcome(
    n_control: int,
    n_treatment: int,
    baseline_rate: float,
    effect_size: float,
    consistent: bool = True,
    seed: Optional[int] = None
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Generate a binary outcome A/B test summary.
    
    Args:
        n_control: Sample size for control group
        n_treatment: Sample size for treatment group
        baseline_rate: Conversion rate for control group
        effect_size: Effect size (lift) for treatment group
        consistent: If True, p-value matches statistical reconstruction
        seed: Random seed for reproducibility
    
    Returns:
        Tuple of (summary_dict, ground_truth_dict)
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
    
    # Calculate treatment rate
    treatment_rate = baseline_rate * (1 + effect_size)
    treatment_rate = min(max(treatment_rate, 0.001), 0.999)
    
    # Generate actual successes
    successes_control = int(n_control * baseline_rate)
    successes_treatment = int(n_treatment * treatment_rate)
    
    # Calculate p-value based on consistency flag
    if consistent:
        # Use two-proportion z-test for consistent p-value
        p_control = successes_control / n_control
        p_treatment = successes_treatment / n_treatment
        pooled_p = (successes_control + successes_treatment) / (n_control + n_treatment)
        
        if pooled_p > 0 and pooled_p < 1:
            se = np.sqrt(pooled_p * (1 - pooled_p) * (1/n_control + 1/n_treatment))
            if se > 0:
                z_stat = (p_treatment - p_control) / se
                p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
            else:
                p_value = 1.0
        else:
            p_value = 1.0
    else:
        # Generate inconsistent p-value (independent of actual data)
        p_value = random.uniform(0.001, 0.5)
    
    # Calculate effect size (reported)
    reported_effect = abs(treatment_rate - baseline_rate) / baseline_rate if baseline_rate > 0 else 0
    
    summary = {
        "outcome_type": "binary",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "baseline_rate": baseline_rate,
        "treatment_rate": treatment_rate,
        "p_value": p_value,
        "effect_size": effect_size,
        "reported_effect_size": reported_effect,
        "test_type": "two_proportion_z",
        "source_url": f"https://example.com/test_{random.randint(10000, 99999)}",
        "domain": random.choice(["tech", "e-commerce", "finance", "healthcare", "saas"]),
        "publication_year": random.randint(2020, 2024),
        "is_consistent": consistent
    }
    
    ground_truth = {
        "true_p_value": p_value if consistent else None,
        "true_effect_size": effect_size,
        "true_baseline_rate": baseline_rate,
        "true_n_control": n_control,
        "true_n_treatment": n_treatment,
        "intentionally_inconsistent": not consistent,
        "inconsistency_reason": "p_value_mismatch" if not consistent else None
    }
    
    return summary, ground_truth

def generate_continuous_outcome(
    n_control: int,
    n_treatment: int,
    baseline_mean: float,
    baseline_std: float,
    effect_size: float,
    consistent: bool = True,
    seed: Optional[int] = None
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Generate a continuous outcome A/B test summary.
    
    Args:
        n_control: Sample size for control group
        n_treatment: Sample size for treatment group
        baseline_mean: Mean for control group
        baseline_std: Standard deviation for control group
        effect_size: Effect size (Cohen's d) for treatment group
        consistent: If True, p-value matches statistical reconstruction
        seed: Random seed for reproducibility
    
    Returns:
        Tuple of (summary_dict, ground_truth_dict)
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
    
    treatment_mean = baseline_mean + (effect_size * baseline_std)
    
    # Generate sample statistics
    if consistent:
        # Use Welch's t-test for consistent p-value
        treatment_std = baseline_std * random.uniform(0.8, 1.2)
        t_stat = (treatment_mean - baseline_mean) / np.sqrt(
            (baseline_std**2 / n_control) + (treatment_std**2 / n_treatment)
        )
        df = (
            ((baseline_std**2 / n_control) + (treatment_std**2 / n_treatment))**2
            / (
                (baseline_std**2 / n_control)**2 / (n_control - 1)
                + (treatment_std**2 / n_treatment)**2 / (n_treatment - 1)
            )
        )
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df))
    else:
        # Generate inconsistent p-value
        p_value = random.uniform(0.001, 0.5)
        treatment_std = baseline_std * random.uniform(0.5, 2.0)
    
    summary = {
        "outcome_type": "continuous",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "baseline_mean": baseline_mean,
        "baseline_std": baseline_std,
        "treatment_mean": treatment_mean,
        "treatment_std": treatment_std,
        "p_value": p_value,
        "effect_size": effect_size,
        "test_type": "welch_t",
        "source_url": f"https://example.com/test_{random.randint(10000, 99999)}",
        "domain": random.choice(["tech", "e-commerce", "finance", "healthcare", "saas"]),
        "publication_year": random.randint(2020, 2024),
        "is_consistent": consistent
    }
    
    ground_truth = {
        "true_p_value": p_value if consistent else None,
        "true_effect_size": effect_size,
        "true_baseline_mean": baseline_mean,
        "true_baseline_std": baseline_std,
        "true_n_control": n_control,
        "true_n_treatment": n_treatment,
        "intentionally_inconsistent": not consistent,
        "inconsistency_reason": "p_value_mismatch" if not consistent else None
    }
    
    return summary, ground_truth

def generate_sample_sizes() -> Tuple[int, int]:
    """Generate realistic sample sizes."""
    base_size = random.randint(MIN_SAMPLE_SIZE, MAX_SAMPLE_SIZE)
    # Add some variation between control and treatment
    n_control = base_size
    n_treatment = int(base_size * random.uniform(0.9, 1.1))
    return n_control, n_treatment

def generate_synthetic_dataset(
    num_binary: int = NUM_BINARY_OUTCOMES,
    num_continuous: int = NUM_CONTINUOUS_OUTCOMES,
    consistent_fraction: float = CONSISTENT_FRACTION,
    seed: int = DEFAULT_SEED
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Generate the complete synthetic dataset.
    
    Args:
        num_binary: Number of binary outcome summaries
        num_continuous: Number of continuous outcome summaries
        consistent_fraction: Fraction of summaries that are statistically consistent
        seed: Random seed for reproducibility
    
    Returns:
        Tuple of (all_summaries, all_ground_truth)
    """
    set_all_seeds(seed)
    
    all_summaries = []
    all_ground_truth = []
    
    # Generate binary outcomes
    logger.info(f"Generating {num_binary} binary outcomes...")
    for i in range(num_binary):
        consistent = random.random() < consistent_fraction
        n_control, n_treatment = generate_sample_sizes()
        baseline_rate = random.uniform(MIN_BASELINE_RATE, MAX_BASELINE_RATE)
        effect_size = random.uniform(MIN_EFFECT_SIZE, MAX_EFFECT_SIZE)
        
        summary, ground_truth = generate_binary_outcome(
            n_control, n_treatment, baseline_rate, effect_size, consistent,
            seed=seed + i if seed else None
        )
        all_summaries.append(summary)
        all_ground_truth.append(ground_truth)
    
    # Generate continuous outcomes
    logger.info(f"Generating {num_continuous} continuous outcomes...")
    for i in range(num_continuous):
        consistent = random.random() < consistent_fraction
        n_control, n_treatment = generate_sample_sizes()
        baseline_mean = random.uniform(1.0, 100.0)
        baseline_std = random.uniform(0.5, baseline_mean * 0.5)
        effect_size = random.uniform(MIN_EFFECT_SIZE, MAX_EFFECT_SIZE)
        
        summary, ground_truth = generate_continuous_outcome(
            n_control, n_treatment, baseline_mean, baseline_std, effect_size, consistent,
            seed=seed + num_binary + i if seed else None
        )
        all_summaries.append(summary)
        all_ground_truth.append(ground_truth)
    
    return all_summaries, all_ground_truth

def write_csv_output(summaries: List[Dict[str, Any]], output_path: Path) -> None:
    """Write summaries to CSV file."""
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        "outcome_type", "n_control", "n_treatment", "baseline_rate",
        "treatment_rate", "baseline_mean", "baseline_std", "treatment_mean",
        "treatment_std", "p_value", "effect_size", "reported_effect_size",
        "test_type", "source_url", "domain", "publication_year", "is_consistent"
    ]
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(summaries)
    
    logger.info(f"Wrote {len(summaries)} summaries to {output_path}")

def write_json_output(
    summaries: List[Dict[str, Any]],
    ground_truth: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """Write ground truth metadata to JSON file."""
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Count outcome types
    binary_count = sum(1 for s in summaries if s["outcome_type"] == "binary")
    continuous_count = sum(1 for s in summaries if s["outcome_type"] == "continuous")
    consistent_count = sum(1 for s in summaries if s["is_consistent"])
    inconsistent_count = len(summaries) - consistent_count
    
    metadata = {
        "total_records": len(summaries),
        "binary_outcomes": binary_count,
        "continuous_outcomes": continuous_count,
        "consistent_summaries": consistent_count,
        "inconsistent_summaries": inconsistent_count,
        "consistent_fraction": consistent_count / len(summaries) if summaries else 0,
        "generation_timestamp": datetime.utcnow().isoformat(),
        "seed": DEFAULT_SEED,
        "ground_truth": ground_truth
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Wrote ground truth metadata to {output_path}")
    logger.info(f"  Total: {metadata['total_records']}")
    logger.info(f"  Binary: {metadata['binary_outcomes']}")
    logger.info(f"  Continuous: {metadata['continuous_outcomes']}")
    logger.info(f"  Consistent: {metadata['consistent_summaries']}")
    logger.info(f"  Inconsistent: {metadata['inconsistent_summaries']}")

def verify_outcome_types(summaries: List[Dict[str, Any]]) -> bool:
    """Verify that both binary and continuous outcomes are present."""
    binary_count = sum(1 for s in summaries if s["outcome_type"] == "binary")
    continuous_count = sum(1 for s in summaries if s["outcome_type"] == "continuous")
    
    has_binary = binary_count > 0
    has_continuous = continuous_count > 0
    
    if has_binary and has_continuous:
        logger.info(f"✓ Both outcome types present: {binary_count} binary, {continuous_count} continuous")
        return True
    else:
        logger.error(f"✗ Missing outcome types: binary={binary_count}, continuous={continuous_count}")
        return False

def main() -> int:
    """Main entry point for synthetic dataset generation."""
    logger.info("Starting synthetic dataset generation...")
    
    try:
        # Generate dataset
        summaries, ground_truth = generate_synthetic_dataset(
            num_binary=NUM_BINARY_OUTCOMES,
            num_continuous=NUM_CONTINUOUS_OUTCOMES,
            consistent_fraction=CONSISTENT_FRACTION,
            seed=DEFAULT_SEED
        )
        
        # Write outputs
        write_csv_output(summaries, CSV_OUTPUT)
        write_json_output(summaries, ground_truth, JSON_OUTPUT)
        
        # Verify outcome types
        if not verify_outcome_types(summaries):
            logger.error("Verification failed: not all outcome types present")
            return 1
        
        # Verify record count
        if len(summaries) < 10000:
            logger.error(f"Verification failed: only {len(summaries)} records, need >= 10000")
            return 1
        
        logger.info("✓ Synthetic dataset generation complete and verified")
        return 0
        
    except Exception as e:
        logger.error(f"Error generating synthetic dataset: {e}")
        raise

if __name__ == "__main__":
    exit(main())
