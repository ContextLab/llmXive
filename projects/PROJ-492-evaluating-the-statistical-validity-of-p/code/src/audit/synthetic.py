"""
Synthetic dataset generator for A/B test summaries (FR-030).

Generates at least 10,000 simulated summaries covering both binary and continuous
outcomes to support validation of the inconsistency detection pipeline.
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

from code.src.config import set_rng_seed, SEED
from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.models.data_models import ABTestSummary

logger = get_default_logger(__name__)

def set_all_seeds(seed: int = SEED) -> None:
    """Seed all random number generators for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)

def generate_sample_sizes(min_n: int = 50, max_n: int = 10000) -> Tuple[int, int]:
    """
    Generate realistic sample sizes for control and treatment groups.
    Uses a log-normal distribution to mimic real-world variance.
    """
    n_control = int(np.random.lognormal(mean=math.log(1000), sigma=0.5))
    n_control = max(min_n, min(n_control, max_n))
    
    # Treatment size often similar but can vary
    ratio = np.random.uniform(0.8, 1.2)
    n_treatment = int(n_control * ratio)
    n_treatment = max(min_n, min(n_treatment, max_n))
    
    return n_control, n_treatment

def generate_binary_outcome(
    n_control: int, 
    n_treatment: int, 
    baseline_rate: float, 
    effect_size: float,
    inject_inconsistency: bool = False
) -> Dict[str, Any]:
    """
    Generate synthetic binary A/B test data.
    
    Args:
        n_control: Sample size of control group
        n_treatment: Sample size of treatment group
        baseline_rate: Expected conversion rate for control (0.0 to 1.0)
        effect_size: True effect size (lift) for treatment
        inject_inconsistency: If True, deliberately mismatch reported stats
    
    Returns:
        Dictionary with observed counts, rates, and calculated p-value.
    """
    # True rates
    p_control = baseline_rate
    p_treatment = baseline_rate * (1 + effect_size)
    # Clamp to valid probability
    p_treatment = max(0.0, min(1.0, p_treatment))
    
    # Simulate outcomes
    x_control = np.random.binomial(n_control, p_control)
    x_treatment = np.random.binomial(n_treatment, p_treatment)
    
    # Observed rates
    rate_control = x_control / n_control
    rate_treatment = x_treatment / n_treatment
    
    # Calculate true p-value using two-proportion z-test
    p_val, _ = stats.proportions_ztest(
        [x_control, x_treatment], 
        [n_control, n_treatment]
    )
    
    reported_p_val = p_val
    reported_effect = (rate_treatment - rate_control)
    
    if inject_inconsistency:
        # Deliberately corrupt the p-value or effect size
        if random.random() > 0.5:
            # Corrupt p-value (make significant when it shouldn't be, or vice versa)
            reported_p_val = random.uniform(0.001, 0.04) if p_val > 0.05 else random.uniform(0.06, 0.2)
        else:
            # Corrupt effect size
            reported_effect = (rate_treatment - rate_control) * random.uniform(1.5, 2.5)
    
    return {
        "n_control": n_control,
        "n_treatment": n_treatment,
        "x_control": int(x_control),
        "x_treatment": int(x_treatment),
        "rate_control": float(rate_control),
        "rate_treatment": float(rate_treatment),
        "true_p_value": float(p_val),
        "reported_p_value": float(reported_p_val),
        "true_effect_size": float(reported_effect if not inject_inconsistency else (rate_treatment - rate_control)),
        "reported_effect_size": float(reported_effect),
        "outcome_type": "binary",
        "is_inconsistent": inject_inconsistency
    }

def generate_continuous_outcome(
    n_control: int,
    n_treatment: int,
    baseline_mean: float,
    baseline_std: float,
    effect_size: float,
    inject_inconsistency: bool = False
) -> Dict[str, Any]:
    """
    Generate synthetic continuous A/B test data.
    
    Args:
        n_control: Sample size of control group
        n_treatment: Sample size of treatment group
        baseline_mean: Mean of control group
        baseline_std: Standard deviation of control group
        effect_size: True effect size (Cohen's d equivalent lift)
        inject_inconsistency: If True, deliberately mismatch reported stats
    
    Returns:
        Dictionary with observed means, stds, and calculated p-value.
    """
    # True parameters
    mean_control = baseline_mean
    mean_treatment = baseline_mean * (1 + effect_size)
    std_control = baseline_std
    # Treatment std might vary slightly
    std_treatment = std_control * np.random.uniform(0.9, 1.1)
    
    # Simulate outcomes
    data_control = np.random.normal(mean_control, std_control, n_control)
    data_treatment = np.random.normal(mean_treatment, std_treatment, n_treatment)
    
    # Observed stats
    obs_mean_control = float(np.mean(data_control))
    obs_mean_treatment = float(np.mean(data_treatment))
    obs_std_control = float(np.std(data_control, ddof=1))
    obs_std_treatment = float(np.std(data_treatment, ddof=1))
    
    # Calculate true p-value using Welch's t-test
    stat, p_val = stats.ttest_ind(data_control, data_treatment, equal_var=False)
    
    reported_p_val = p_val
    reported_effect = obs_mean_treatment - obs_mean_control
    
    if inject_inconsistency:
        if random.random() > 0.5:
            reported_p_val = random.uniform(0.001, 0.04) if p_val > 0.05 else random.uniform(0.06, 0.2)
        else:
            reported_effect = (obs_mean_treatment - obs_mean_control) * random.uniform(1.5, 2.5)
    
    return {
        "n_control": n_control,
        "n_treatment": n_treatment,
        "mean_control": obs_mean_control,
        "mean_treatment": obs_mean_treatment,
        "std_control": obs_std_control,
        "std_treatment": obs_std_treatment,
        "true_p_value": float(p_val),
        "reported_p_value": float(reported_p_val),
        "true_effect_size": float(obs_mean_treatment - obs_mean_control),
        "reported_effect_size": float(reported_effect),
        "outcome_type": "continuous",
        "is_inconsistent": inject_inconsistency
    }

def generate_synthetic_dataset(
    total_records: int = 10000,
    binary_ratio: float = 0.6,
    inconsistency_rate: float = 0.15,
    output_dir: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Generate the full synthetic dataset.
    
    Args:
        total_records: Total number of summaries to generate (minimum 10,000 per FR-030)
        binary_ratio: Proportion of binary outcomes (default 60%)
        inconsistency_rate: Proportion of records with injected inconsistencies
        output_dir: Directory to write output files (default: data/synthetic)
    
    Returns:
        List of generated summary dictionaries.
    """
    if total_records < 10000:
        logger.warning(f"Requested {total_records} records, but FR-030 requires >= 10,000. Adjusting to 10,000.")
        total_records = 10000
    
    set_all_seeds()
    
    num_binary = int(total_records * binary_ratio)
    num_continuous = total_records - num_binary
    
    records = []
    
    # Generate binary records
    for i in range(num_binary):
        n_c, n_t = generate_sample_sizes()
        base_rate = np.random.uniform(0.05, 0.30)
        effect = np.random.choice([-0.1, 0.0, 0.05, 0.1, 0.2], p=[0.1, 0.1, 0.4, 0.3, 0.1])
        inject = random.random() < inconsistency_rate
        
        record = generate_binary_outcome(n_c, n_t, base_rate, effect, inject)
        record["id"] = f"syn_bin_{i:06d}"
        record["domain"] = random.choice(["ecommerce", "marketing", "social", "news"])
        record["year"] = random.randint(2018, 2024)
        records.append(record)
    
    # Generate continuous records
    for i in range(num_continuous):
        n_c, n_t = generate_sample_sizes(min_n=100, max_n=5000)
        base_mean = np.random.uniform(10.0, 100.0)
        base_std = base_mean * np.random.uniform(0.3, 0.8)
        effect = np.random.choice([-0.1, 0.0, 0.05, 0.1, 0.2], p=[0.1, 0.1, 0.4, 0.3, 0.1])
        inject = random.random() < inconsistency_rate
        
        record = generate_continuous_outcome(n_c, n_t, base_mean, base_std, effect, inject)
        record["id"] = f"syn_cont_{i:06d}"
        record["domain"] = random.choice(["saas", "gaming", "fintech", "health"])
        record["year"] = random.randint(2018, 2024)
        records.append(record)
    
    # Shuffle to mix types
    random.shuffle(records)
    
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        write_csv_output(records, output_dir / "synthetic_summaries.csv")
        write_json_output(records, output_dir / "synthetic_summaries.json")
        write_metadata(len(records), num_binary, num_continuous, output_dir / "synthetic_metadata.json")
    
    return records

def verify_outcome_types(records: List[Dict[str, Any]]) -> Tuple[int, int, bool]:
    """
    Verify that both binary and continuous outcomes are present.
    
    Returns:
        Tuple of (binary_count, continuous_count, both_present)
    """
    binary_count = sum(1 for r in records if r.get("outcome_type") == "binary")
    continuous_count = sum(1 for r in records if r.get("outcome_type") == "continuous")
    both_present = binary_count > 0 and continuous_count > 0
    return binary_count, continuous_count, both_present

def write_csv_output(records: List[Dict[str, Any]], filepath: Path) -> None:
    """Write records to CSV file."""
    if not records:
        return
    
    fieldnames = list(records[0].keys())
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    logger.info(f"Wrote {len(records)} records to {filepath}")

def write_json_output(records: List[Dict[str, Any]], filepath: Path) -> None:
    """Write records to JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2)
    logger.info(f"Wrote {len(records)} records to {filepath}")

def write_metadata(
    total: int, 
    binary: int, 
    continuous: int, 
    filepath: Path
) -> None:
    """Write generation metadata."""
    meta = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_records": total,
        "binary_count": binary,
        "continuous_count": continuous,
        "both_types_present": binary > 0 and continuous > 0,
        "seed": SEED
    }
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=2)
    logger.info(f"Wrote metadata to {filepath}")

def main() -> None:
    """Main entry point for synthetic dataset generation."""
    logger.info("Starting synthetic dataset generation (T026)...")
    
    output_dir = Path("data/synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate dataset
    records = generate_synthetic_dataset(
        total_records=10000,
        binary_ratio=0.6,
        inconsistency_rate=0.15,
        output_dir=output_dir
    )
    
    # Verify requirements
    binary_count, continuous_count, both_present = verify_outcome_types(records)
    
    if not both_present:
        logger.error("FAILED: Both outcome types not present!")
        raise RuntimeError("Synthetic dataset missing outcome types")
    
    if len(records) < 10000:
        logger.error(f"FAILED: Only {len(records)} records generated, need >= 10,000")
        raise RuntimeError("Insufficient records generated")
    
    logger.info(f"SUCCESS: Generated {len(records)} records (Binary: {binary_count}, Continuous: {continuous_count})")
    logger.info(f"Output files written to: {output_dir}")

if __name__ == "__main__":
    main()
