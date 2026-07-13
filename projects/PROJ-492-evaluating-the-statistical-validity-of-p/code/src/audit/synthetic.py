"""
Synthetic dataset generator for A/B test validity evaluation.

Implements FR-030: Generate synthetic A/B test summaries with known ground truth
for binary and continuous outcomes. Ensures constraint preservation (constraint-preservation-2958f04c)
by generating statistically consistent data where reported p-values match reconstructed values.

Output:
  - data/synthetic/binary_outcomes.csv (>= 10,000 records)
  - data/synthetic/continuous_outcomes.csv (>= 10,000 records)
  - data/synthetic/ground_truth.json (validation labels)
"""
import json
import logging
import math
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
from scipy import stats

from code.src.config import set_rng_seed, SEED
from code.src.utils.logger import get_default_logger

# Ensure output directories exist
OUTPUT_DIR = Path("data/synthetic")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

logger = get_default_logger(__name__)

def generate_binary_summary(
    n_control: int,
    n_treatment: int,
    p_control: float,
    p_treatment: float,
    seed: Optional[int] = None
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Generate a synthetic binary outcome A/B test summary.
    
    Returns:
      summary: Dict with extracted-like fields (n_control, n_treatment, 
               control_rate, treatment_rate, reported_p_value, etc.)
      ground_truth: Dict with true parameters and expected p-value
    """
    if seed is not None:
        np.random.seed(seed)
        random.seed(seed)
    
    # Simulate actual outcomes
    control_successes = np.random.binomial(n_control, p_control)
    treatment_successes = np.random.binomial(n_treatment, p_treatment)
    
    control_rate = control_successes / n_control
    treatment_rate = treatment_successes / n_treatment
    
    # Calculate true p-value using two-proportion z-test
    pooled_p = (control_successes + treatment_successes) / (n_control + n_treatment)
    se = math.sqrt(pooled_p * (1 - pooled_p) * (1/n_control + 1/n_treatment))
    if se > 0:
        z_stat = (treatment_rate - control_rate) / se
        true_p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    else:
        true_p_value = 1.0
    
    # Apply small random noise to reported p-value to simulate real-world reporting
    noise = np.random.normal(0, 0.001)
    reported_p_value = max(0.0, min(1.0, true_p_value + noise))
    
    summary = {
        "url": f"https://example.com/test_{random.randint(10000, 99999)}",
        "domain": "example.com",
        "test_type": "binary",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "control_rate": round(control_rate, 6),
        "treatment_rate": round(treatment_rate, 6),
        "reported_p_value": round(reported_p_value, 6),
        "effect_size": round(treatment_rate - control_rate, 6),
        "confidence_interval_lower": None,
        "confidence_interval_upper": None,
        "publication_year": random.randint(2020, 2025),
        "is_significant": reported_p_value < 0.05
    }
    
    ground_truth = {
        "true_p_control": p_control,
        "true_p_treatment": p_treatment,
        "true_p_value": round(true_p_value, 6),
        "expected_significant": true_p_value < 0.05,
        "noise_applied": round(noise, 6),
        "is_consistent": abs(reported_p_value - true_p_value) < 0.05
    }
    
    return summary, ground_truth

def generate_continuous_summary(
    n_control: int,
    n_treatment: int,
    mu_control: float,
    mu_treatment: float,
    sigma: float,
    seed: Optional[int] = None
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Generate a synthetic continuous outcome A/B test summary.
    
    Returns:
      summary: Dict with extracted-like fields
      ground_truth: Dict with true parameters and expected p-value
    """
    if seed is not None:
        np.random.seed(seed)
        random.seed(seed)
    
    # Simulate actual outcomes
    control_data = np.random.normal(mu_control, sigma, n_control)
    treatment_data = np.random.normal(mu_treatment, sigma, n_treatment)
    
    control_mean = float(np.mean(control_data))
    treatment_mean = float(np.mean(treatment_data))
    control_std = float(np.std(control_data, ddof=1))
    treatment_std = float(np.std(treatment_data, ddof=1))
    
    # Calculate true p-value using Welch's t-test
    t_stat, true_p_value = stats.ttest_ind(
        treatment_data, control_data, equal_var=False
    )
    true_p_value = float(true_p_value)
    
    # Apply small random noise to reported p-value
    noise = np.random.normal(0, 0.001)
    reported_p_value = max(0.0, min(1.0, true_p_value + noise))
    
    summary = {
        "url": f"https://example.com/test_{random.randint(10000, 99999)}",
        "domain": "example.com",
        "test_type": "continuous",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "control_mean": round(control_mean, 6),
        "treatment_mean": round(treatment_mean, 6),
        "control_std": round(control_std, 6),
        "treatment_std": round(treatment_std, 6),
        "reported_p_value": round(reported_p_value, 6),
        "effect_size": round(treatment_mean - control_mean, 6),
        "confidence_interval_lower": None,
        "confidence_interval_upper": None,
        "publication_year": random.randint(2020, 2025),
        "is_significant": reported_p_value < 0.05
    }
    
    ground_truth = {
        "true_mu_control": mu_control,
        "true_mu_treatment": mu_treatment,
        "true_sigma": sigma,
        "true_p_value": round(true_p_value, 6),
        "expected_significant": true_p_value < 0.05,
        "noise_applied": round(noise, 6),
        "is_consistent": abs(reported_p_value - true_p_value) < 0.05
    }
    
    return summary, ground_truth

def generate_synthetic_dataset(
    n_records: int = 10000,
    seed: int = SEED
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Generate a large synthetic dataset of A/B test summaries.
    
    Args:
        n_records: Number of records to generate (minimum 10,000)
        seed: Random seed for reproducibility
    """
    set_rng_seed(seed)
    
    summaries = []
    ground_truths = []
    
    # Generate binary outcomes (60% of dataset)
    n_binary = int(n_records * 0.6)
    for i in range(n_binary):
        # Vary parameters to create diverse dataset
        n_control = random.randint(100, 5000)
        n_treatment = random.randint(100, 5000)
        p_control = random.uniform(0.05, 0.5)
        # Effect size: mostly small, some medium, few large
        effect_choice = random.random()
        if effect_choice < 0.7:
            effect = random.uniform(-0.05, 0.05)
        elif effect_choice < 0.9:
            effect = random.uniform(-0.1, 0.1)
        else:
            effect = random.uniform(-0.2, 0.2)
        p_treatment = max(0.0, min(1.0, p_control + effect))
        
        summary, gt = generate_binary_summary(n_control, n_treatment, p_control, p_treatment, seed=seed+i)
        summaries.append(summary)
        ground_truths.append(gt)
    
    # Generate continuous outcomes (40% of dataset)
    n_continuous = n_records - n_binary
    for i in range(n_continuous):
        n_control = random.randint(50, 2000)
        n_treatment = random.randint(50, 2000)
        mu_control = random.uniform(10, 100)
        sigma = random.uniform(5, 20)
        effect_choice = random.random()
        if effect_choice < 0.7:
            effect = random.uniform(-2, 2)
        elif effect_choice < 0.9:
            effect = random.uniform(-5, 5)
        else:
            effect = random.uniform(-10, 10)
        mu_treatment = mu_control + effect
        
        summary, gt = generate_continuous_summary(n_control, n_treatment, mu_control, mu_treatment, sigma, seed=seed+n_binary+i)
        summaries.append(summary)
        ground_truths.append(gt)
    
    return summaries, ground_truths

def write_csv(summaries: List[Dict[str, Any]], filepath: Path) -> None:
    """Write summaries to CSV file."""
    if not summaries:
        logger.warning("No summaries to write to CSV")
        return
    
    keys = summaries[0].keys()
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(summaries)
    logger.info(f"Wrote {len(summaries)} records to {filepath}")

def write_json(data: List[Dict[str, Any]], filepath: Path) -> None:
    """Write ground truth to JSON file."""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Wrote {len(data)} ground truth records to {filepath}")

def main():
    """Entry point for synthetic data generation."""
    logger.info("Starting synthetic dataset generation")
    
    # Generate at least 10,000 records as required by FR-030
    n_records = 12000  # Generate extra to ensure >= 10,000 after any filtering
    summaries, ground_truths = generate_synthetic_dataset(n_records=n_records, seed=SEED)
    
    # Write binary outcomes
    binary_summaries = [s for s in summaries if s['test_type'] == 'binary']
    binary_path = OUTPUT_DIR / "binary_outcomes.csv"
    write_csv(binary_summaries, binary_path)
    
    # Write continuous outcomes
    continuous_summaries = [s for s in summaries if s['test_type'] == 'continuous']
    continuous_path = OUTPUT_DIR / "continuous_outcomes.csv"
    write_csv(continuous_summaries, continuous_path)
    
    # Write ground truth
    ground_truth_path = OUTPUT_DIR / "ground_truth.json"
    write_json(ground_truths, ground_truth_path)
    
    # Log statistics
    logger.info(f"Total binary records: {len(binary_summaries)}")
    logger.info(f"Total continuous records: {len(continuous_summaries)}")
    logger.info(f"Total records: {len(summaries)}")
    
    # Verify constraint preservation
    consistent_count = sum(1 for gt in ground_truths if gt['is_consistent'])
    consistency_rate = consistent_count / len(ground_truths) if ground_truths else 0
    logger.info(f"Constraint preservation rate: {consistency_rate:.2%} ({consistent_count}/{len(ground_truths)})")
    
    if consistency_rate < 0.95:
        logger.warning(f"Constraint preservation rate {consistency_rate:.2%} is below expected threshold")
    
    logger.info("Synthetic dataset generation completed successfully")
    return 0

if __name__ == "__main__":
    import csv
    import sys
    sys.exit(main())
