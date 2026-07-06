"""
Synthetic Dataset Generator (FR-030).

Generates a synthetic corpus of A/B test summaries for validation purposes.
Outputs at least 10,000 records containing both binary and continuous outcomes.
"""
import csv
import json
import logging
import random
import math
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Import from project API surface
from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.models.data_models import ABTestSummary

logger = get_default_logger(__name__)


def set_all_seeds(seed: int = SEED) -> None:
    """Seed all random number generators for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    logger.info(f"Seeded RNGs with seed={seed}")


def generate_sample_sizes(min_n: int = 50, max_n: int = 5000) -> Tuple[int, int]:
    """
    Generate realistic sample sizes for control and treatment groups.
    Returns (n_control, n_treatment).
    """
    # Use log-normal distribution for more realistic sample size variance
    log_mean = math.log(500)
    log_std = 0.8
    
    n_control = int(max(min_n, min(max_n, random.lognormvariate(log_mean, log_std))))
    # Treatment size often similar but can vary
    ratio = random.uniform(0.8, 1.2)
    n_treatment = int(max(min_n, min(max_n, n_control * ratio)))
    
    return n_control, n_treatment


def generate_binary_outcome(
    n_control: int, 
    n_treatment: int, 
    baseline_rate: float, 
    effect_size: float,
    is_inconsistent: bool = False
) -> Dict[str, Any]:
    """
    Generate binary outcome metrics (conversion rates).
    
    Args:
        n_control: Sample size of control group
        n_treatment: Sample size of treatment group
        baseline_rate: True conversion rate for control (0.0-1.0)
        effect_size: True lift (e.g., 0.05 for 5% lift)
        is_inconsistent: If True, report a p-value that contradicts the data
    
    Returns:
        Dictionary with metrics for binary outcome
    """
    # Calculate true rates
    rate_control = baseline_rate
    rate_treatment = baseline_rate * (1 + effect_size)
    
    # Clamp rates to valid range
    rate_treatment = max(0.0, min(1.0, rate_treatment))
    
    # Simulate successes (binomial)
    successes_control = int(n_control * rate_control)
    successes_treatment = int(n_treatment * rate_treatment)
    
    # Calculate observed rates
    obs_rate_control = successes_control / n_control
    obs_rate_treatment = successes_treatment / n_treatment
    
    # Calculate observed lift
    obs_lift = (obs_rate_treatment - obs_rate_control) / obs_rate_control if obs_rate_control > 0 else 0.0
    
    # Calculate standard error for z-test
    p_pooled = (successes_control + successes_treatment) / (n_control + n_treatment)
    se = math.sqrt(p_pooled * (1 - p_pooled) * (1/n_control + 1/n_treatment))
    
    # Calculate z-statistic
    if se > 0:
        z_stat = (obs_rate_treatment - obs_rate_control) / se
    else:
        z_stat = 0.0
    
    # Calculate p-value (two-tailed)
    p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(z_stat) / math.sqrt(2))))
    
    # Inject inconsistency if requested
    if is_inconsistent:
        # Report a p-value that suggests significance when it's not, or vice versa
        # Flip the significance: if p < 0.05, report p > 0.10, and vice versa
        if p_value < 0.05:
            reported_p = random.uniform(0.15, 0.50)
        else:
            reported_p = random.uniform(0.01, 0.04)
    else:
        reported_p = p_value
    
    return {
        "n_control": n_control,
        "n_treatment": n_treatment,
        "successes_control": successes_control,
        "successes_treatment": successes_treatment,
        "rate_control": obs_rate_control,
        "rate_treatment": obs_rate_treatment,
        "lift": obs_lift,
        "p_value": reported_p,
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
    Generate continuous outcome metrics (means and standard deviations).
    
    Args:
        n_control: Sample size of control group
        n_treatment: Sample size of treatment group
        baseline_mean: True mean for control
        baseline_std: True standard deviation for control
        effect_size: True difference in means (absolute)
        is_inconsistent: If True, report a p-value that contradicts the data
    
    Returns:
        Dictionary with metrics for continuous outcome
    """
    # Calculate true means
    mean_control = baseline_mean
    mean_treatment = baseline_mean + effect_size
    
    # Assume similar variance for simplicity (can be extended)
    std_control = baseline_std
    std_treatment = baseline_std * random.uniform(0.9, 1.1)
    
    # Simulate data (normal distribution)
    # We don't need to generate the raw data, just the summary stats
    # But to be realistic, we simulate the sample means and sds
    
    # Standard error of the mean
    se_control = std_control / math.sqrt(n_control)
    se_treatment = std_treatment / math.sqrt(n_treatment)
    
    # Simulate observed means (add small noise to true mean)
    obs_mean_control = mean_control + random.gauss(0, se_control * 0.5)
    obs_mean_treatment = mean_treatment + random.gauss(0, se_treatment * 0.5)
    
    # Simulate observed standard deviations (chi-square variation)
    # Simplified: just add small noise
    obs_std_control = std_control * random.uniform(0.95, 1.05)
    obs_std_treatment = std_treatment * random.uniform(0.95, 1.05)
    
    # Calculate observed difference
    diff = obs_mean_treatment - obs_mean_control
    
    # Calculate Welch's t-statistic
    se_diff = math.sqrt((obs_std_control**2 / n_control) + (obs_std_treatment**2 / n_treatment))
    
    if se_diff > 0:
        t_stat = diff / se_diff
    else:
        t_stat = 0.0
    
    # Degrees of freedom (Welch-Satterthwaite equation)
    num = (obs_std_control**2 / n_control + obs_std_treatment**2 / n_treatment)**2
    denom = (
        (obs_std_control**2 / n_control)**2 / (n_control - 1) +
        (obs_std_treatment**2 / n_treatment)**2 / (n_treatment - 1)
    )
    df = num / denom if denom > 0 else (n_control + n_treatment - 2)
    
    # Calculate p-value (two-tailed)
    # Use normal approximation for large df, otherwise use t-distribution logic
    if df > 100:
        p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(t_stat) / math.sqrt(2))))
    else:
        # Approximate using scipy logic if available, else normal approx
        # For synthetic generation, normal approx is usually sufficient for large N
        p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(t_stat) / math.sqrt(2))))
    
    # Inject inconsistency if requested
    if is_inconsistent:
        if p_value < 0.05:
            reported_p = random.uniform(0.15, 0.50)
        else:
            reported_p = random.uniform(0.01, 0.04)
    else:
        reported_p = p_value
    
    return {
        "n_control": n_control,
        "n_treatment": n_treatment,
        "mean_control": obs_mean_control,
        "mean_treatment": obs_mean_treatment,
        "std_control": obs_std_control,
        "std_treatment": obs_std_treatment,
        "difference": diff,
        "p_value": reported_p,
        "is_inconsistent": is_inconsistent
    }


def generate_synthetic_dataset(
    total_records: int = 10000,
    binary_ratio: float = 0.6,
    inconsistency_rate: float = 0.15,
    seed: int = SEED
) -> List[Dict[str, Any]]:
    """
    Generate a synthetic dataset of A/B test summaries.
    
    Args:
        total_records: Total number of records to generate (default 10,000)
        binary_ratio: Proportion of records that are binary outcomes (default 0.6)
        inconsistency_rate: Proportion of records with inconsistent p-values (default 0.15)
        seed: Random seed for reproducibility
    
    Returns:
        List of dictionaries representing ABTestSummary records
    """
    set_all_seeds(seed)
    
    records = []
    binary_count = int(total_records * binary_ratio)
    continuous_count = total_records - binary_count
    
    # Common domains for variety
    domains = ["ecommerce", "media", "fintech", "health", "education", "social", "gaming"]
    years = list(range(2018, 2025))
    
    logger.info(f"Generating {binary_count} binary and {continuous_count} continuous records...")
    
    # Generate Binary Outcomes
    for i in range(binary_count):
        n_control, n_treatment = generate_sample_sizes()
        baseline_rate = random.uniform(0.01, 0.20) # 1% to 20% conversion
        effect_size = random.choice([random.uniform(0.01, 0.10), random.uniform(-0.05, 0.05)])
        is_inconsistent = random.random() < inconsistency_rate
        
        metrics = generate_binary_outcome(
            n_control, n_treatment, baseline_rate, effect_size, is_inconsistent
        )
        
        record = {
            "id": f"syn_binary_{i:05d}",
            "outcome_type": "binary",
            "domain": random.choice(domains),
            "year": random.choice(years),
            "is_inconsistent": is_inconsistent,
            **metrics
        }
        records.append(record)
    
    # Generate Continuous Outcomes
    for i in range(continuous_count):
        n_control, n_treatment = generate_sample_sizes(100, 2000) # Often larger N for continuous
        baseline_mean = random.uniform(10.0, 100.0)
        baseline_std = random.uniform(5.0, 30.0)
        effect_size = random.choice([random.uniform(1.0, 10.0), random.uniform(-5.0, 5.0)])
        is_inconsistent = random.random() < inconsistency_rate
        
        metrics = generate_continuous_outcome(
            n_control, n_treatment, baseline_mean, baseline_std, effect_size, is_inconsistent
        )
        
        record = {
            "id": f"syn_cont_{i:05d}",
            "outcome_type": "continuous",
            "domain": random.choice(domains),
            "year": random.choice(years),
            "is_inconsistent": is_inconsistent,
            **metrics
        }
        records.append(record)
    
    # Shuffle to mix types
    random.shuffle(records)
    
    logger.info(f"Generated {len(records)} synthetic records.")
    return records


def verify_outcome_types(records: List[Dict[str, Any]]) -> Tuple[int, int]:
    """
    Verify that both binary and continuous outcomes are present.
    
    Returns:
        Tuple of (binary_count, continuous_count)
    """
    binary_count = sum(1 for r in records if r.get("outcome_type") == "binary")
    continuous_count = sum(1 for r in records if r.get("outcome_type") == "continuous")
    
    if binary_count == 0:
        raise ValueError("Verification failed: No binary outcomes found.")
    if continuous_count == 0:
        raise ValueError("Verification failed: No continuous outcomes found.")
    
    logger.info(f"Verification passed: {binary_count} binary, {continuous_count} continuous.")
    return binary_count, continuous_count


def write_csv_output(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Write synthetic dataset to CSV."""
    if not records:
        raise ValueError("No records to write.")
    
    # Flatten nested dicts if any (our records are flat)
    fieldnames = list(records[0].keys())
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    
    logger.info(f"Wrote CSV to {output_path}")


def write_json_output(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Write synthetic dataset to JSON."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    
    logger.info(f"Wrote JSON to {output_path}")


def write_metadata(output_dir: Path, binary_count: int, continuous_count: int) -> None:
    """Write generation metadata."""
    metadata = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_records": binary_count + continuous_count,
        "binary_count": binary_count,
        "continuous_count": continuous_count,
        "seed": SEED,
        "task_id": "T026"
    }
    
    metadata_path = output_dir / "synthetic_metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Wrote metadata to {metadata_path}")


def main() -> None:
    """Main entry point for synthetic dataset generation."""
    # Define output paths relative to project root
    # Ensure we use the 'data' directory as per project structure
    output_dir = Path("data") / "synthetic"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    csv_path = output_dir / "synthetic_summaries.csv"
    json_path = output_dir / "synthetic_summaries.json"
    
    try:
        # Generate dataset
        records = generate_synthetic_dataset(total_records=10000)
        
        # Verify outcome types
        binary_count, continuous_count = verify_outcome_types(records)
        
        if binary_count + continuous_count < 10000:
            raise ValueError(f"Record count {binary_count + continuous_count} is less than required 10,000.")
        
        # Write outputs
        write_csv_output(records, csv_path)
        write_json_output(records, json_path)
        write_metadata(output_dir, binary_count, continuous_count)
        
        logger.info("Synthetic dataset generation completed successfully.")
        
    except Exception as e:
        logger.error(f"Failed to generate synthetic dataset: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
