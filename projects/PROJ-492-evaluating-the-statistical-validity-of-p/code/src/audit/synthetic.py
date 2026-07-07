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

from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.models.data_models import ABTestSummary

logger = get_default_logger(__name__)

# Configuration constants
MIN_TOTAL_RECORDS = 10000
BINARY_RATIO = 0.5  # 50% binary, 50% continuous
MIN_SAMPLE_SIZE = 50
MAX_SAMPLE_SIZE = 5000
BASELINE_RANGE = (0.05, 0.50)
EFFECT_SIZE_RANGE = (-0.15, 0.15)
NOISE_SCALE = 0.02
DOMAINS = ["tech", "finance", "health", "retail", "education"]
YEARS = list(range(2018, 2025))

def set_all_seeds(seed: int = SEED) -> None:
    """Set seeds for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Seeds set to {seed}")

def generate_sample_sizes(n: int) -> List[int]:
    """Generate random sample sizes for n records."""
    return [random.randint(MIN_SAMPLE_SIZE, MAX_SAMPLE_SIZE) for _ in range(n)]

def generate_binary_outcome(
    n_control: int,
    n_treatment: int,
    baseline_rate: float,
    effect_size: float
) -> Tuple[int, int, int, int, float]:
    """
    Generate binary outcome data (successes/failures) for control and treatment.
    Returns: (control_successes, control_failures, treatment_successes, treatment_failures, true_p)
    """
    treatment_rate = baseline_rate + effect_size
    # Ensure rates are valid probabilities
    treatment_rate = max(0.0, min(1.0, treatment_rate))

    control_successes = np.random.binomial(n_control, baseline_rate)
    treatment_successes = np.random.binomial(n_treatment, treatment_rate)

    control_failures = n_control - control_successes
    treatment_failures = n_treatment - treatment_successes

    # Calculate true p-value using two-proportion z-test
    p1 = control_successes / n_control
    p2 = treatment_successes / n_treatment
    pooled_p = (control_successes + treatment_successes) / (n_control + n_treatment)
    
    if pooled_p == 0 or pooled_p == 1:
        true_p = 1.0
    else:
        se = np.sqrt(pooled_p * (1 - pooled_p) * (1/n_control + 1/n_treatment))
        z_stat = (p1 - p2) / se if se > 0 else 0.0
        true_p = 2 * (1 - abs(stats.norm.cdf(abs(z_stat))))
    
    return int(control_successes), int(control_failures), int(treatment_successes), int(treatment_failures), float(true_p)

def generate_continuous_outcome(
    n_control: int,
    n_treatment: int,
    baseline_mean: float,
    effect_size: float,
    std_dev: float
) -> Tuple[List[float], List[float], float]:
    """
    Generate continuous outcome data for control and treatment.
    Returns: (control_data, treatment_data, true_p)
    """
    treatment_mean = baseline_mean + effect_size
    
    control_data = np.random.normal(baseline_mean, std_dev, n_control)
    treatment_data = np.random.normal(treatment_mean, std_dev, n_treatment)
    
    # Calculate true p-value using Welch's t-test
    stat, true_p = stats.ttest_ind(control_data, treatment_data, equal_var=False)
    
    return control_data.tolist(), treatment_data.tolist(), float(true_p)

def generate_synthetic_dataset(
    total_records: int = MIN_TOTAL_RECORDS,
    seed: int = SEED
) -> List[Dict[str, Any]]:
    """
    Generate a synthetic dataset of A/B test summaries.
    Ensures both binary and continuous outcomes are present.
    """
    set_all_seeds(seed)
    
    summaries = []
    binary_count = 0
    continuous_count = 0
    
    # Ensure we have at least some of each type
    n_binary = max(int(total_records * BINARY_RATIO), 100)
    n_continuous = total_records - n_binary
    
    logger.info(f"Generating {n_binary} binary and {n_continuous} continuous records")
    
    # Generate binary outcomes
    for i in range(n_binary):
        n_control = random.randint(MIN_SAMPLE_SIZE, MAX_SAMPLE_SIZE)
        n_treatment = random.randint(MIN_SAMPLE_SIZE, MAX_SAMPLE_SIZE)
        baseline = random.uniform(*BASELINE_RANGE)
        effect = random.uniform(*EFFECT_SIZE_RANGE)
        
        c_succ, c_fail, t_succ, t_fail, true_p = generate_binary_outcome(
            n_control, n_treatment, baseline, effect
        )
        
        summary = {
            "id": f"synthetic_binary_{i:05d}",
            "outcome_type": "binary",
            "n_control": n_control,
            "n_treatment": n_treatment,
            "control_successes": c_succ,
            "control_failures": c_fail,
            "treatment_successes": t_succ,
            "treatment_failures": t_fail,
            "baseline_rate": baseline,
            "effect_size": effect,
            "reported_p_value": true_p,
            "domain": random.choice(DOMAINS),
            "year": random.choice(YEARS),
            "is_consistent": True,
            "source_url": f"https://example.com/synthetic/binary/{i}"
        }
        summaries.append(summary)
        binary_count += 1
    
    # Generate continuous outcomes
    for i in range(n_continuous):
        n_control = random.randint(MIN_SAMPLE_SIZE, MAX_SAMPLE_SIZE)
        n_treatment = random.randint(MIN_SAMPLE_SIZE, MAX_SAMPLE_SIZE)
        baseline_mean = random.uniform(10.0, 100.0)
        effect = random.uniform(-5.0, 5.0)
        std_dev = random.uniform(2.0, 10.0)
        
        c_data, t_data, true_p = generate_continuous_outcome(
            n_control, n_treatment, baseline_mean, effect, std_dev
        )
        
        # Calculate summary statistics
        c_mean = float(np.mean(c_data))
        t_mean = float(np.mean(t_data))
        c_std = float(np.std(c_data))
        t_std = float(np.std(t_data))
        
        summary = {
            "id": f"synthetic_continuous_{i:05d}",
            "outcome_type": "continuous",
            "n_control": n_control,
            "n_treatment": n_treatment,
            "control_mean": c_mean,
            "treatment_mean": t_mean,
            "control_std": c_std,
            "treatment_std": t_std,
            "baseline_mean": baseline_mean,
            "effect_size": effect,
            "reported_p_value": true_p,
            "domain": random.choice(DOMAINS),
            "year": random.choice(YEARS),
            "is_consistent": True,
            "source_url": f"https://example.com/synthetic/continuous/{i}"
        }
        summaries.append(summary)
        continuous_count += 1
    
    logger.info(f"Generated {binary_count} binary and {continuous_count} continuous records")
    return summaries

def verify_outcome_types(summaries: List[Dict[str, Any]]) -> Tuple[int, int]:
    """Verify that both outcome types are present and count them."""
    binary_count = sum(1 for s in summaries if s["outcome_type"] == "binary")
    continuous_count = sum(1 for s in summaries if s["outcome_type"] == "continuous")
    
    if binary_count == 0:
        raise ValueError("No binary outcomes found in generated dataset")
    if continuous_count == 0:
        raise ValueError("No continuous outcomes found in generated dataset")
    
    logger.info(f"Verification passed: {binary_count} binary, {continuous_count} continuous")
    return binary_count, continuous_count

def write_metadata(metadata: Dict[str, Any], output_path: Path) -> None:
    """Write generation metadata to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Metadata written to {output_path}")

def write_summaries(summaries: List[Dict[str, Any]], output_path: Path) -> None:
    """Write summaries to CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not summaries:
        raise ValueError("Cannot write empty summaries list")
    
    fieldnames = list(summaries[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)
    
    logger.info(f"Wrote {len(summaries)} summaries to {output_path}")

def main() -> None:
    """Main entry point for synthetic dataset generation."""
    output_dir = Path("data") / "synthetic"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate dataset
    summaries = generate_synthetic_dataset(total_records=MIN_TOTAL_RECORDS, seed=SEED)
    
    # Verify outcome types
    binary_count, continuous_count = verify_outcome_types(summaries)
    
    if len(summaries) < MIN_TOTAL_RECORDS:
        raise ValueError(f"Generated only {len(summaries)} records, expected at least {MIN_TOTAL_RECORDS}")
    
    # Write outputs
    csv_path = output_dir / "synthetic_summaries.csv"
    write_summaries(summaries, csv_path)
    
    metadata = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_records": len(summaries),
        "binary_count": binary_count,
        "continuous_count": continuous_count,
        "seed": SEED,
        "min_sample_size": MIN_SAMPLE_SIZE,
        "max_sample_size": MAX_SAMPLE_SIZE,
        "domains": DOMAINS,
        "years": YEARS
    }
    
    metadata_path = output_dir / "synthetic_metadata.json"
    write_metadata(metadata, metadata_path)
    
    logger.info(f"Synthetic dataset generation complete: {len(summaries)} records")
    logger.info(f"Binary: {binary_count}, Continuous: {continuous_count}")
    logger.info(f"Output files: {csv_path}, {metadata_path}")

if __name__ == "__main__":
    main()
