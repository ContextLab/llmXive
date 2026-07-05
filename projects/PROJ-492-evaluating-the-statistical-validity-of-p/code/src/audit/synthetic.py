"""
Synthetic dataset generator for A/B test validation (FR-030).
Generates 10,000+ simulated A/B test summaries with both binary and continuous outcomes.
Outputs:
  - data/synthetic/synthetic_validation.csv: The synthetic summaries for pipeline ingestion.
  - data/synthetic/synthetic_ground_truth.json: The ground truth metadata for evaluation.
"""
import csv
import json
import logging
import random
import math
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Literal

import numpy as np
from scipy import stats

# Import project configuration for deterministic seeding
from code.src.config import set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger

# Constants
NUM_RECORDS = 10000
BINARY_RATIO = 0.5  # 50% binary, 50% continuous
OUTPUT_DIR = Path("data/synthetic")
CSV_OUTPUT = OUTPUT_DIR / "synthetic_validation.csv"
JSON_OUTPUT = OUTPUT_DIR / "synthetic_ground_truth.json"

logger = get_default_logger(__name__)

def set_all_seeds(seed: int = 42) -> None:
    """Set random seeds for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Seeds set to {seed}")

def generate_sample_sizes() -> Tuple[int, int]:
    """Generate realistic sample sizes for control and treatment groups."""
    # Sample sizes typically range from 100 to 10,000
    n_control = int(np.random.lognormal(mean=4.5, sigma=0.8))
    n_treatment = int(np.random.lognormal(mean=4.5, sigma=0.8))
    # Ensure minimum sample size
    n_control = max(50, n_control)
    n_treatment = max(50, n_treatment)
    return n_control, n_treatment

def generate_binary_outcome(n_control: int, n_treatment: int, 
                            baseline_rate: float, effect_size: float,
                            inject_inconsistency: bool = False) -> Dict[str, Any]:
    """
    Generate binary outcome data (clicks, conversions).
    Returns observed metrics and ground truth.
    """
    # True rates
    p_control = baseline_rate
    p_treatment = baseline_rate * (1 + effect_size)
    p_treatment = max(0.0, min(1.0, p_treatment))

    # Simulate successes
    successes_control = np.random.binomial(n_control, p_control)
    successes_treatment = np.random.binomial(n_treatment, p_treatment)

    observed_rate_control = successes_control / n_control
    observed_rate_treatment = successes_treatment / n_treatment
    
    observed_effect = observed_rate_treatment - observed_rate_control
    observed_effect_pct = (observed_rate_treatment / observed_rate_control - 1) if observed_rate_control > 0 else 0.0

    # Calculate p-value (Two-proportion z-test)
    # Using scipy for accurate p-value calculation
    stat, p_value = stats.proportions_ztest(
        [successes_control, successes_treatment], 
        [n_control, n_treatment]
    )

    # Inject inconsistency if requested
    reported_p_value = p_value
    reported_effect_size = observed_effect_pct
    
    if inject_inconsistency:
        # Flip the significance or distort the effect size
        if p_value < 0.05:
            reported_p_value = 0.08 # Make significant appear non-significant
        else:
            reported_p_value = 0.03 # Make non-significant appear significant
        
        # Distort effect size by 10-20%
        distortion = 1.0 + (np.random.uniform(0.1, 0.2) * np.random.choice([-1, 1]))
        reported_effect_size = observed_effect_pct * distortion

    return {
        "n_control": n_control,
        "n_treatment": n_treatment,
        "successes_control": int(successes_control),
        "successes_treatment": int(successes_treatment),
        "rate_control": observed_rate_control,
        "rate_treatment": observed_rate_treatment,
        "p_value_reported": reported_p_value,
        "effect_size_reported": reported_effect_size,
        "ground_truth_p_value": p_value,
        "ground_truth_effect_pct": observed_effect_pct,
        "is_inconsistent": inject_inconsistency
    }

def generate_continuous_outcome(n_control: int, n_treatment: int,
                                baseline_mean: float, baseline_std: float,
                                effect_size: float, inject_inconsistency: bool = False) -> Dict[str, Any]:
    """
    Generate continuous outcome data (revenue, time on site).
    Returns observed metrics and ground truth.
    """
    # True parameters
    mu_control = baseline_mean
    mu_treatment = baseline_mean * (1 + effect_size)
    
    # Ensure positive means if baseline is positive
    if baseline_mean > 0:
        mu_treatment = max(0.01, mu_treatment)

    sigma = baseline_std

    # Simulate data
    data_control = np.random.normal(mu_control, sigma, n_control)
    data_treatment = np.random.normal(mu_treatment, sigma, n_treatment)

    mean_control = np.mean(data_control)
    mean_treatment = np.mean(data_treatment)
    std_control = np.std(data_control, ddof=1)
    std_treatment = np.std(data_treatment, ddof=1)

    observed_effect = mean_treatment - mean_control
    observed_effect_pct = (mean_treatment / mean_control - 1) if mean_control != 0 else 0.0

    # Calculate p-value (Welch's t-test)
    stat, p_value = stats.ttest_ind(data_control, data_treatment, equal_var=False)

    # Inject inconsistency
    reported_p_value = p_value
    reported_effect_size = observed_effect_pct

    if inject_inconsistency:
        if p_value < 0.05:
            reported_p_value = 0.08
        else:
            reported_p_value = 0.03
        distortion = 1.0 + (np.random.uniform(0.1, 0.2) * np.random.choice([-1, 1]))
        reported_effect_size = observed_effect_pct * distortion

    return {
        "n_control": n_control,
        "n_treatment": n_treatment,
        "mean_control": float(mean_control),
        "mean_treatment": float(mean_treatment),
        "std_control": float(std_control),
        "std_treatment": float(std_treatment),
        "p_value_reported": reported_p_value,
        "effect_size_reported": reported_effect_size,
        "ground_truth_p_value": p_value,
        "ground_truth_effect_pct": observed_effect_pct,
        "is_inconsistent": inject_inconsistency
    }

def generate_synthetic_dataset(num_records: int = NUM_RECORDS) -> Tuple[List[Dict], List[Dict]]:
    """
    Generate the full synthetic dataset.
    Returns: (summaries_list, ground_truth_list)
    """
    summaries = []
    ground_truth = []
    
    # Domain list for variety
    domains = ["ecommerce", "saaS", "media", "finance", "healthcare"]
    
    for i in range(num_records):
        is_binary = random.random() < BINARY_RATIO
        inject_inconsistency = random.random() < 0.15 # 15% inconsistency rate
        
        n_c, n_t = generate_sample_sizes()
        domain = random.choice(domains)
        
        record_id = f"syn_{i:05d}"
        
        if is_binary:
            # Binary parameters
            base_rate = np.random.uniform(0.05, 0.30)
            effect = np.random.choice([-0.1, -0.05, 0.0, 0.05, 0.1]) * np.random.choice([0.5, 1.0, 1.5])
            
            data = generate_binary_outcome(n_c, n_t, base_rate, effect, inject_inconsistency)
            
            summary = {
                "id": record_id,
                "outcome_type": "binary",
                "domain": domain,
                "n_control": data["n_control"],
                "n_treatment": data["n_treatment"],
                "metric_control": data["rate_control"],
                "metric_treatment": data["rate_treatment"],
                "p_value": data["p_value_reported"],
                "effect_size_pct": data["effect_size_reported"],
                "test_type": "z-test",
                "is_significant": data["p_value_reported"] < 0.05
            }
            gt = {
                "id": record_id,
                "type": "binary",
                "ground_truth": {
                    "p_value": data["ground_truth_p_value"],
                    "effect_pct": data["ground_truth_effect_pct"],
                    "successes_control": data["successes_control"],
                    "successes_treatment": data["successes_treatment"]
                },
                "is_inconsistent": data["is_inconsistent"]
            }
        else:
            # Continuous parameters
            base_mean = np.random.uniform(10.0, 100.0)
            base_std = base_mean * np.random.uniform(0.3, 0.6) # CV ~ 30-60%
            effect = np.random.choice([-0.1, -0.05, 0.0, 0.05, 0.1]) * np.random.choice([0.5, 1.0, 1.5])
            
            data = generate_continuous_outcome(n_c, n_t, base_mean, base_std, effect, inject_inconsistency)
            
            summary = {
                "id": record_id,
                "outcome_type": "continuous",
                "domain": domain,
                "n_control": data["n_control"],
                "n_treatment": data["n_treatment"],
                "metric_control": data["mean_control"],
                "metric_treatment": data["mean_treatment"],
                "std_control": data["std_control"],
                "std_treatment": data["std_treatment"],
                "p_value": data["p_value_reported"],
                "effect_size_pct": data["effect_size_reported"],
                "test_type": "welch-t",
                "is_significant": data["p_value_reported"] < 0.05
            }
            gt = {
                "id": record_id,
                "type": "continuous",
                "ground_truth": {
                    "p_value": data["ground_truth_p_value"],
                    "effect_pct": data["ground_truth_effect_pct"],
                    "mean_control": data["mean_control"],
                    "mean_treatment": data["mean_treatment"]
                },
                "is_inconsistent": data["is_inconsistent"]
            }
        
        summaries.append(summary)
        ground_truth.append(gt)

    return summaries, ground_truth

def write_csv_output(summaries: List[Dict], filepath: Path) -> None:
    """Write synthetic summaries to CSV."""
    if not summaries:
        raise ValueError("No summaries to write.")
    
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = list(summaries[0].keys())
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)
    
    logger.info(f"Wrote {len(summaries)} records to {filepath}")

def write_json_output(ground_truth: List[Dict], filepath: Path) -> None:
    """Write ground truth metadata to JSON."""
    if not ground_truth:
        raise ValueError("No ground truth to write.")
    
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_records": len(ground_truth),
        "records": ground_truth
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Wrote ground truth for {len(ground_truth)} records to {filepath}")

def verify_outcome_types(summaries: List[Dict]) -> Tuple[int, int]:
    """Verify that both binary and continuous outcomes are present."""
    binary_count = sum(1 for s in summaries if s.get("outcome_type") == "binary")
    continuous_count = sum(1 for s in summaries if s.get("outcome_type") == "continuous")
    
    logger.info(f"Verification: Binary={binary_count}, Continuous={continuous_count}, Total={len(summaries)}")
    
    if binary_count == 0:
        raise ValueError("Generated dataset contains NO binary outcomes.")
    if continuous_count == 0:
        raise ValueError("Generated dataset contains NO continuous outcomes.")
    
    return binary_count, continuous_count

def main():
    """Main entry point for synthetic dataset generation."""
    logger.info("Starting synthetic dataset generation...")
    set_all_seeds(42)
    
    try:
        summaries, ground_truth = generate_synthetic_dataset(NUM_RECORDS)
        
        # Verify outcome types
        b_count, c_count = verify_outcome_types(summaries)
        if b_count + c_count < NUM_RECORDS:
            raise ValueError(f"Record count mismatch: {b_count + c_count} < {NUM_RECORDS}")
        
        # Write outputs
        write_csv_output(summaries, CSV_OUTPUT)
        write_json_output(ground_truth, JSON_OUTPUT)
        
        logger.info("Synthetic dataset generation completed successfully.")
        
    except Exception as e:
        logger.error(f"Failed to generate synthetic dataset: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
