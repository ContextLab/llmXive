"""
Synthetic Dataset Generator (FR-030)

Generates a synthetic dataset of A/B test summaries for validation purposes.
Outputs at least 10,000 simulated summaries covering both binary and continuous outcomes.
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

# Constants
MIN_RECORDS = 10000
BINARY_RATIO = 0.5  # 50% binary, 50% continuous
DOMAINS = ["tech", "finance", "health", "retail", "education"]
YEARS = list(range(2018, 2025))

logger = get_default_logger(__name__)

def set_all_seeds(seed: int = SEED) -> None:
    """Set all random seeds for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)

def generate_sample_sizes(n_total: int) -> Tuple[int, int]:
    """Generate realistic sample sizes for control and treatment groups."""
    # Sample sizes usually vary between 100 and 10,000
    base_n = np.random.lognormal(mean=6, sigma=1)  # Log-normal distribution
    n_control = int(max(100, min(10000, base_n)))
    # Treatment group is usually similar, sometimes slightly different
    ratio = np.random.uniform(0.8, 1.2)
    n_treatment = int(max(100, min(10000, n_control * ratio)))
    return n_control, n_treatment

def generate_binary_outcome(
    n_control: int, n_treatment: int, base_rate: float, effect_size: float, is_inconsistent: bool = False
) -> Dict[str, Any]:
    """
    Generate binary outcome data (conversion rates).
    Returns control_successes, treatment_successes, control_rate, treatment_rate, p_value, effect_size_observed.
    """
    # Generate successes based on rates
    control_rate = base_rate
    treatment_rate = base_rate * (1 + effect_size)
    # Clamp rates to [0, 1]
    treatment_rate = max(0.0, min(1.0, treatment_rate))

    control_successes = int(np.random.binomial(n_control, control_rate))
    treatment_successes = int(np.random.binomial(n_treatment, treatment_rate))

    # Calculate p-value using two-proportion z-test
    # If inconsistent, we might manipulate the p-value or effect size to create a discrepancy
    if is_inconsistent:
        # Introduce a discrepancy: report a p-value that doesn't match the data
        # For example, if the data is significant, report non-significant, or vice versa
        # Here we just add noise to the reported p-value
        true_p = stats.proportions_ztest(
            [control_successes, treatment_successes],
            [n_control, n_treatment]
        )[1]
        # Add noise to create inconsistency (e.g., flip significance or shift p-value)
        reported_p = true_p + np.random.uniform(-0.08, 0.08)
        reported_p = max(0.0, min(1.0, reported_p))
    else:
        reported_p = stats.proportions_ztest(
            [control_successes, treatment_successes],
            [n_control, n_treatment]
        )[1]

    effect_size_observed = (treatment_rate - control_rate) / control_rate if control_rate > 0 else 0.0

    return {
        "n_control": n_control,
        "n_treatment": n_treatment,
        "control_successes": control_successes,
        "treatment_successes": treatment_successes,
        "control_rate": control_rate,
        "treatment_rate": treatment_rate,
        "p_value": reported_p,
        "effect_size": effect_size_observed,
        "is_binary": True
    }

def generate_continuous_outcome(
    n_control: int, n_treatment: int, base_mean: float, base_std: float, effect_size: float, is_inconsistent: bool = False
) -> Dict[str, Any]:
    """
    Generate continuous outcome data (means and standard deviations).
    Returns mean_control, mean_treatment, std_control, std_treatment, p_value, effect_size_observed.
    """
    # Generate means
    mean_control = base_mean
    mean_treatment = base_mean * (1 + effect_size)

    # Standard deviations (usually around 10-30% of mean)
    std_control = base_std
    std_treatment = base_std * np.random.uniform(0.8, 1.2)

    if is_inconsistent:
        # Generate true p-value from Welch's t-test
        true_p = stats.ttest_ind_from_stats(
            mean_control, std_control, n_control,
            mean_treatment, std_treatment, n_treatment, equal_var=False
        )[1]
        # Introduce inconsistency
        reported_p = true_p + np.random.uniform(-0.08, 0.08)
        reported_p = max(0.0, min(1.0, reported_p))
    else:
        reported_p = stats.ttest_ind_from_stats(
            mean_control, std_control, n_control,
            mean_treatment, std_treatment, n_treatment, equal_var=False
        )[1]

    effect_size_observed = (mean_treatment - mean_control) / std_control if std_control > 0 else 0.0

    return {
        "n_control": n_control,
        "n_treatment": n_treatment,
        "mean_control": mean_control,
        "mean_treatment": mean_treatment,
        "std_control": std_control,
        "std_treatment": std_treatment,
        "p_value": reported_p,
        "effect_size": effect_size_observed,
        "is_binary": False
    }

def generate_synthetic_dataset(n_records: int = MIN_RECORDS) -> List[Dict[str, Any]]:
    """Generate the full synthetic dataset."""
    set_all_seeds()
    records = []
    n_binary = int(n_records * BINARY_RATIO)
    n_continuous = n_records - n_binary

    logger.info(f"Generating {n_binary} binary and {n_continuous} continuous records.")

    # Generate binary outcomes
    for i in range(n_binary):
        n_c, n_t = generate_sample_sizes(n_records)
        base_rate = np.random.uniform(0.01, 0.5)
        effect_size = np.random.choice([-0.2, -0.1, 0, 0.1, 0.2], p=[0.1, 0.2, 0.4, 0.2, 0.1])
        # 10% of records are inconsistent
        is_inconsistent = np.random.random() < 0.1
        data = generate_binary_outcome(n_c, n_t, base_rate, effect_size, is_inconsistent)
        
        record = {
            "id": f"synthetic_bin_{i:05d}",
            "domain": random.choice(DOMAINS),
            "year": random.choice(YEARS),
            "outcome_type": "binary",
            **data,
            "inconsistent": is_inconsistent
        }
        records.append(record)

    # Generate continuous outcomes
    for i in range(n_continuous):
        n_c, n_t = generate_sample_sizes(n_records)
        base_mean = np.random.uniform(10, 100)
        base_std = np.random.uniform(5, 20)
        effect_size = np.random.choice([-0.2, -0.1, 0, 0.1, 0.2], p=[0.1, 0.2, 0.4, 0.2, 0.1])
        is_inconsistent = np.random.random() < 0.1
        data = generate_continuous_outcome(n_c, n_t, base_mean, base_std, effect_size, is_inconsistent)

        record = {
            "id": f"synthetic_cont_{i:05d}",
            "domain": random.choice(DOMAINS),
            "year": random.choice(YEARS),
            "outcome_type": "continuous",
            **data,
            "inconsistent": is_inconsistent
        }
        records.append(record)

    return records

def write_csv_output(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Write synthetic dataset to CSV."""
    if not records:
        raise ValueError("No records to write.")
    
    # Flatten nested dictionaries if any (our records are already flat)
    fieldnames = list(records[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    
    logger.info(f"Wrote {len(records)} records to {output_path}")

def write_json_output(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Write synthetic dataset to JSON."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2)
    logger.info(f"Wrote {len(records)} records to {output_path}")

def verify_outcome_types(records: List[Dict[str, Any]]) -> Tuple[int, int]:
    """Verify that both binary and continuous outcomes are present."""
    binary_count = sum(1 for r in records if r.get("outcome_type") == "binary" or r.get("is_binary") is True)
    continuous_count = sum(1 for r in records if r.get("outcome_type") == "continuous" or r.get("is_binary") is False)
    
    if binary_count == 0:
        raise ValueError("No binary outcomes found in the dataset.")
    if continuous_count == 0:
        raise ValueError("No continuous outcomes found in the dataset.")
    
    logger.info(f"Verification passed: {binary_count} binary, {continuous_count} continuous outcomes.")
    return binary_count, continuous_count

def main() -> None:
    """Main entry point for synthetic dataset generation."""
    output_dir = Path("data/synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    csv_path = output_dir / "synthetic_summaries.csv"
    json_path = output_dir / "synthetic_summaries.json"
    
    # Generate dataset
    records = generate_synthetic_dataset(MIN_RECORDS)
    
    # Verify outcome types
    verify_outcome_types(records)
    
    # Write outputs
    write_csv_output(records, csv_path)
    write_json_output(records, json_path)
    
    logger.info(f"Synthetic dataset generation complete. Total records: {len(records)}")

if __name__ == "__main__":
    main()
