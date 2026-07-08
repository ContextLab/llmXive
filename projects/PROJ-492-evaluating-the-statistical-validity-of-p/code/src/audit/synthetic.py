"""
Synthetic dataset generator for A/B test validation (FR-030).

Generates at least 10,000 simulated summaries with both binary and continuous outcomes.
Verifies that both outcome types are present in the generated dataset.
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

from code.src.config import set_rng_seed, SEED
from code.src.models.data_models import ABTestSummary
from code.src.utils.logger import get_default_logger, AuditLogger

# Constants
TOTAL_RECORDS = 10000
BINARY_RATIO = 0.5  # 50% binary, 50% continuous
MIN_SAMPLE_SIZE = 50
MAX_SAMPLE_SIZE = 10000
BASELINE_MIN = 0.05
BASELINE_MAX = 0.95
EFFECT_SIZE_MIN = 0.01
EFFECT_SIZE_MAX = 0.30

logger = get_default_logger(__name__)


def set_all_seeds(seed: int = SEED) -> None:
    """Set all random seeds for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Random seeds set to {seed}")


def generate_sample_sizes(n: int, min_size: int = MIN_SAMPLE_SIZE, max_size: int = MAX_SAMPLE_SIZE) -> np.ndarray:
    """Generate sample sizes from a log-normal distribution."""
    # Log-normal distribution for realistic sample size variation
    log_mean = np.log(np.sqrt(min_size * max_size))
    log_std = 1.0
    sizes = np.random.lognormal(log_mean, log_std, n)
    sizes = np.clip(sizes, min_size, max_size).astype(int)
    return sizes


def generate_binary_outcome(
    n_control: int,
    n_treatment: int,
    baseline_rate: float,
    effect_size: float,
    is_inconsistent: bool = False
) -> Tuple[int, int, int, int, float, float]:
    """
    Generate binary outcome data (conversions).
    
    Returns:
        (n_control, success_control, n_treatment, success_treatment, reported_p, true_p)
    """
    # Calculate treatment rate
    treatment_rate = baseline_rate + effect_size
    treatment_rate = np.clip(treatment_rate, 0.0, 1.0)
    
    # Generate successes
    success_control = np.random.binomial(n_control, baseline_rate)
    success_treatment = np.random.binomial(n_treatment, treatment_rate)
    
    # Calculate true p-value using two-proportion z-test
    pooled_p = (success_control + success_treatment) / (n_control + n_treatment)
    se = np.sqrt(pooled_p * (1 - pooled_p) * (1/n_control + 1/n_treatment))
    z_stat = (treatment_rate - baseline_rate) / se if se > 0 else 0
    true_p = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    
    # If inconsistent, perturb the reported p-value
    if is_inconsistent:
        # Add noise to create inconsistency (e.g., 10-20% deviation)
        perturbation = np.random.uniform(0.10, 0.25)
        reported_p = true_p * (1 + perturbation * np.random.choice([-1, 1]))
        reported_p = np.clip(reported_p, 0.001, 0.999)
    else:
        reported_p = true_p
    
    return n_control, success_control, n_treatment, success_treatment, float(reported_p), float(true_p)


def generate_continuous_outcome(
    n_control: int,
    n_treatment: int,
    baseline_mean: float,
    effect_size: float,
    std_dev: float = 1.0,
    is_inconsistent: bool = False
) -> Tuple[float, float, float, float, float, float]:
    """
    Generate continuous outcome data (means and variances).
    
    Returns:
        (n_control, mean_control, n_treatment, mean_treatment, reported_p, true_p)
    """
    treatment_mean = baseline_mean + effect_size * std_dev
    
    # Generate sample means (approximate by sampling and taking mean)
    control_data = np.random.normal(baseline_mean, std_dev, n_control)
    treatment_data = np.random.normal(treatment_mean, std_dev, n_treatment)
    
    mean_control = np.mean(control_data)
    mean_treatment = np.mean(treatment_data)
    std_control = np.std(control_data, ddof=1)
    std_treatment = np.std(treatment_data, ddof=1)
    
    # Calculate true p-value using Welch's t-test
    true_p = stats.ttest_ind(
        control_data, treatment_data, equal_var=False
    ).pvalue
    
    # If inconsistent, perturb the reported p-value
    if is_inconsistent:
        perturbation = np.random.uniform(0.10, 0.25)
        reported_p = true_p * (1 + perturbation * np.random.choice([-1, 1]))
        reported_p = np.clip(reported_p, 0.001, 0.999)
    else:
        reported_p = true_p
    
    return float(mean_control), float(mean_treatment), float(std_control), float(std_treatment), float(reported_p), float(true_p)


def generate_synthetic_dataset(
    n_records: int = TOTAL_RECORDS,
    output_dir: str = "data",
    seed: int = SEED
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Generate a synthetic dataset of A/B test summaries.
    
    Args:
        n_records: Number of records to generate (minimum 10,000)
        output_dir: Directory to write output files
        seed: Random seed for reproducibility
    
    Returns:
        Tuple of (list of summary dicts, metadata dict)
    """
    set_all_seeds(seed)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    summaries = []
    metadata = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_records": n_records,
        "seed": seed,
        "outcome_types": {"binary": 0, "continuous": 0},
        "inconsistent_count": 0,
        "consistent_count": 0
    }
    
    # Generate sample sizes
    sample_sizes = generate_sample_sizes(n_records)
    
    # Determine outcome types (50/50 split)
    outcome_types = np.random.choice(
        ["binary", "continuous"], 
        size=n_records, 
        p=[BINARY_RATIO, 1 - BINARY_RATIO]
    )
    
    # Determine inconsistency (~15% inconsistent)
    inconsistency_flags = np.random.random(n_records) < 0.15
    
    for i in range(n_records):
        outcome_type = outcome_types[i]
        is_inconsistent = inconsistency_flags[i]
        n_control = sample_sizes[i]
        n_treatment = sample_sizes[i]
        
        # Generate domain and year
        domains = ["tech", "e-commerce", "finance", "health", "education"]
        domain = random.choice(domains)
        year = random.randint(2020, 2024)
        
        if outcome_type == "binary":
            baseline_rate = np.random.uniform(BASELINE_MIN, BASELINE_MAX)
            effect_size = np.random.uniform(EFFECT_SIZE_MIN, EFFECT_SIZE_MAX)
            if random.random() < 0.5:
                effect_size *= -1  # 50% chance of negative effect
            
            n_c, s_c, n_t, s_t, rep_p, true_p = generate_binary_outcome(
                n_control, n_treatment, baseline_rate, effect_size, is_inconsistent
            )
            
            summary = {
                "id": f"syn_{i:06d}",
                "domain": domain,
                "year": year,
                "outcome_type": "binary",
                "n_control": n_c,
                "n_treatment": n_t,
                "success_control": s_c,
                "success_treatment": s_t,
                "baseline_rate": float(baseline_rate),
                "treatment_rate": float(s_t / n_t),
                "effect_size": float((s_t / n_t) - (s_c / n_c)),
                "reported_p_value": rep_p,
                "reconstructed_p_value": true_p,
                "is_inconsistent": is_inconsistent
            }
            metadata["outcome_types"]["binary"] += 1
        
        else:  # continuous
            baseline_mean = np.random.uniform(10.0, 100.0)
            effect_size = np.random.uniform(EFFECT_SIZE_MIN, EFFECT_SIZE_MAX) * 10
            if random.random() < 0.5:
                effect_size *= -1
            std_dev = np.random.uniform(5.0, 20.0)
            
            mean_c, mean_t, std_c, std_t, rep_p, true_p = generate_continuous_outcome(
                n_control, n_treatment, baseline_mean, effect_size, std_dev, is_inconsistent
            )
            
            summary = {
                "id": f"syn_{i:06d}",
                "domain": domain,
                "year": year,
                "outcome_type": "continuous",
                "n_control": n_control,
                "n_treatment": n_treatment,
                "mean_control": mean_c,
                "mean_treatment": mean_t,
                "std_control": std_c,
                "std_treatment": std_t,
                "baseline_mean": baseline_mean,
                "effect_size": float(mean_t - mean_c),
                "reported_p_value": rep_p,
                "reconstructed_p_value": true_p,
                "is_inconsistent": is_inconsistent
            }
            metadata["outcome_types"]["continuous"] += 1
        
        if is_inconsistent:
            metadata["inconsistent_count"] += 1
        else:
            metadata["consistent_count"] += 1
        
        summaries.append(summary)
    
    # Write outputs
    write_summaries(summaries, output_path / "synthetic_summaries.csv")
    write_metadata(metadata, output_path / "synthetic_metadata.json")
    
    logger.info(f"Generated {len(summaries)} synthetic summaries")
    logger.info(f"Binary outcomes: {metadata['outcome_types']['binary']}")
    logger.info(f"Continuous outcomes: {metadata['outcome_types']['continuous']}")
    
    return summaries, metadata


def verify_outcome_types(summaries: List[Dict[str, Any]]) -> bool:
    """
    Verify that both binary and continuous outcomes are present.
    
    Args:
        summaries: List of generated summary dictionaries
    
    Returns:
        True if both types are present, False otherwise
    """
    outcome_types = set(s["outcome_type"] for s in summaries)
    has_binary = "binary" in outcome_types
    has_continuous = "continuous" in outcome_types
    
    if has_binary and has_continuous:
        logger.info("Verification passed: Both binary and continuous outcomes present")
        return True
    else:
        missing = []
        if not has_binary:
            missing.append("binary")
        if not has_continuous:
            missing.append("continuous")
        logger.error(f"Verification failed: Missing outcome types: {missing}")
        return False


def write_summaries(summaries: List[Dict[str, Any]], output_path: Path) -> None:
    """Write summaries to CSV file."""
    if not summaries:
        raise ValueError("Cannot write empty summaries list")
    
    fieldnames = list(summaries[0].keys())
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)
    
    logger.info(f"Wrote {len(summaries)} summaries to {output_path}")


def write_metadata(metadata: Dict[str, Any], output_path: Path) -> None:
    """Write metadata to JSON file."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Wrote metadata to {output_path}")


def main() -> None:
    """Main entry point for synthetic dataset generation."""
    try:
        logger.info("Starting synthetic dataset generation")
        
        summaries, metadata = generate_synthetic_dataset(
            n_records=TOTAL_RECORDS,
            output_dir="data",
            seed=SEED
        )
        
        # Verify outcome types
        if not verify_outcome_types(summaries):
            raise RuntimeError("Verification failed: Not all outcome types present")
        
        logger.info("Synthetic dataset generation completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to generate synthetic dataset: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
