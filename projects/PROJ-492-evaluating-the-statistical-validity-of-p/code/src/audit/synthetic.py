"""
Synthetic dataset generator for A/B test validation (FR-030).
Generates 10,000+ simulated summaries with both binary and continuous outcomes.
"""
import csv
import json
import logging
import random
import math
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
from scipy import stats

from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger

logger = get_default_logger(__name__)

# Configuration constants
TOTAL_RECORDS = 10000
BINARY_RATIO = 0.5  # 50% binary, 50% continuous
MIN_SAMPLE_SIZE = 50
MAX_SAMPLE_SIZE = 5000
BASELINE_RATE_MIN = 0.05
BASELINE_RATE_MAX = 0.50
EFFECT_SIZE_MIN = 0.01
EFFECT_SIZE_MAX = 0.20
CONTINUOUS_MEAN_MIN = 10.0
CONTINUOUS_MEAN_MAX = 100.0
CONTINUOUS_STD_MIN = 5.0
CONTINUOUS_STD_MAX = 30.0

def set_all_seeds(seed: int = SEED) -> None:
    """Set random seeds for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Random seeds set to {seed}")

def generate_sample_sizes(n: int) -> Tuple[List[int], List[int]]:
    """Generate sample sizes for control and treatment groups."""
    control_sizes = []
    treatment_sizes = []
    for _ in range(n):
        # Generate base size with some variation
        base_size = random.randint(MIN_SAMPLE_SIZE, MAX_SAMPLE_SIZE)
        # Allow treatment size to vary slightly from control
        variation = random.uniform(0.8, 1.2)
        control_sizes.append(base_size)
        treatment_sizes.append(int(base_size * variation))
    return control_sizes, treatment_sizes

def generate_binary_outcome(
    n: int,
    control_size: int,
    treatment_size: int,
    baseline_rate: float,
    effect_size: float,
    inject_inconsistency: bool = False
) -> Dict[str, Any]:
    """
    Generate binary outcome A/B test data.
    
    Args:
        n: Record index
        control_size: Control group sample size
        treatment_size: Treatment group sample size
        baseline_rate: Control conversion rate
        effect_size: True effect size (treatment - control)
        inject_inconsistency: Whether to intentionally create inconsistency
    
    Returns:
        Dictionary with synthetic A/B test summary
    """
    treatment_rate = baseline_rate + effect_size
    
    # Ensure rates are within valid bounds
    treatment_rate = max(0.0, min(1.0, treatment_rate))
    
    # Generate observed successes
    control_successes = int(control_size * baseline_rate)
    treatment_successes = int(treatment_size * treatment_rate)
    
    # Calculate p-value using two-proportion z-test
    # Add small noise to create realistic variation
    noise = random.gauss(0, 0.001)
    
    if inject_inconsistency:
        # Inject inconsistency by distorting p-value
        true_p_value = stats.norm.cdf(-abs(effect_size) / math.sqrt(
            baseline_rate * (1 - baseline_rate) / control_size +
            treatment_rate * (1 - treatment_rate) / treatment_size
        ))
        # Distort the reported p-value
        reported_p_value = max(0.001, min(0.999, true_p_value * random.uniform(0.5, 2.0)))
    else:
        # Calculate true p-value
        p_control = control_successes / control_size
        p_treatment = treatment_successes / treatment_size
        
        # Pooled proportion for z-test
        pooled_p = (control_successes + treatment_successes) / (control_size + treatment_size)
        se = math.sqrt(pooled_p * (1 - pooled_p) * (1/control_size + 1/treatment_size))
        
        if se > 0:
            z_stat = (p_treatment - p_control) / se
            reported_p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
        else:
            reported_p_value = 1.0
        
        reported_p_value = max(0.001, min(0.999, reported_p_value))
    
    return {
        "record_id": n,
        "outcome_type": "binary",
        "control_sample_size": control_size,
        "treatment_sample_size": treatment_size,
        "control_successes": control_successes,
        "treatment_successes": treatment_successes,
        "control_rate": round(control_successes / control_size, 6),
        "treatment_rate": round(treatment_successes / treatment_size, 6),
        "reported_p_value": round(reported_p_value, 6),
        "effect_size": round(effect_size, 6),
        "baseline_rate": round(baseline_rate, 6),
        "is_inconsistent": inject_inconsistency
    }

def generate_continuous_outcome(
    n: int,
    control_size: int,
    treatment_size: int,
    control_mean: float,
    treatment_mean: float,
    control_std: float,
    treatment_std: float,
    inject_inconsistency: bool = False
) -> Dict[str, Any]:
    """
    Generate continuous outcome A/B test data.
    
    Args:
        n: Record index
        control_size: Control group sample size
        treatment_size: Treatment group sample size
        control_mean: Control group mean
        treatment_mean: Treatment group mean
        control_std: Control group standard deviation
        treatment_std: Treatment group standard deviation
        inject_inconsistency: Whether to intentionally create inconsistency
    
    Returns:
        Dictionary with synthetic A/B test summary
    """
    # Calculate true p-value using Welch's t-test approximation
    se_diff = math.sqrt((control_std**2 / control_size) + (treatment_std**2 / treatment_size))
    true_diff = treatment_mean - control_mean
    
    if se_diff > 0:
        t_stat = true_diff / se_diff
        # Welch-Satterthwaite degrees of freedom approximation
        df_num = (control_std**2 / control_size + treatment_std**2 / treatment_size)**2
        df_den = (control_std**4 / (control_size**2 * (control_size - 1)) + 
                 treatment_std**4 / (treatment_size**2 * (treatment_size - 1)))
        df = df_num / df_den if df_den > 0 else 100
        
        true_p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df))
    else:
        true_p_value = 1.0
    
    if inject_inconsistency:
        # Distort the reported p-value
        reported_p_value = max(0.001, min(0.999, true_p_value * random.uniform(0.3, 3.0)))
    else:
        reported_p_value = max(0.001, min(0.999, true_p_value))
    
    return {
        "record_id": n,
        "outcome_type": "continuous",
        "control_sample_size": control_size,
        "treatment_sample_size": treatment_size,
        "control_mean": round(control_mean, 4),
        "treatment_mean": round(treatment_mean, 4),
        "control_std": round(control_std, 4),
        "treatment_std": round(treatment_std, 4),
        "reported_p_value": round(reported_p_value, 6),
        "effect_size": round(treatment_mean - control_mean, 6),
        "is_inconsistent": inject_inconsistency
    }

def generate_synthetic_dataset(
    total_records: int = TOTAL_RECORDS,
    inconsistency_rate: float = 0.15
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Generate a complete synthetic dataset with both binary and continuous outcomes.
    
    Args:
        total_records: Total number of records to generate
        inconsistency_rate: Proportion of records with intentional inconsistencies
    
    Returns:
        Tuple of (records list, ground truth metadata)
    """
    set_all_seeds()
    
    records = []
    ground_truth = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_records": total_records,
        "inconsistency_rate": inconsistency_rate,
        "outcome_types": {},
        "parameters": {
            "min_sample_size": MIN_SAMPLE_SIZE,
            "max_sample_size": MAX_SAMPLE_SIZE,
            "baseline_rate_range": [BASELINE_RATE_MIN, BASELINE_RATE_MAX],
            "effect_size_range": [EFFECT_SIZE_MIN, EFFECT_SIZE_MAX]
        }
    }
    
    # Calculate distribution
    binary_count = int(total_records * BINARY_RATIO)
    continuous_count = total_records - binary_count
    
    # Generate sample sizes once
    control_sizes, treatment_sizes = generate_sample_sizes(total_records)
    
    # Generate binary outcomes
    binary_inconsistent = 0
    for i in range(binary_count):
        inject_inconsistency = random.random() < inconsistency_rate
        if inject_inconsistency:
            binary_inconsistent += 1
        
        baseline_rate = random.uniform(BASELINE_RATE_MIN, BASELINE_RATE_MAX)
        effect_size = random.choice([-1, 1]) * random.uniform(EFFECT_SIZE_MIN, EFFECT_SIZE_MAX)
        
        record = generate_binary_outcome(
            n=i,
            control_size=control_sizes[i],
            treatment_size=treatment_sizes[i],
            baseline_rate=baseline_rate,
            effect_size=effect_size,
            inject_inconsistency=inject_inconsistency
        )
        records.append(record)
    
    ground_truth["outcome_types"]["binary"] = {
        "count": binary_count,
        "inconsistent_count": binary_inconsistent,
        "consistent_count": binary_count - binary_inconsistent
    }
    
    # Generate continuous outcomes
    continuous_inconsistent = 0
    for i in range(continuous_count):
        idx = binary_count + i
        inject_inconsistency = random.random() < inconsistency_rate
        if inject_inconsistency:
            continuous_inconsistent += 1
        
        control_mean = random.uniform(CONTINUOUS_MEAN_MIN, CONTINUOUS_MEAN_MAX)
        effect_size = random.choice([-1, 1]) * random.uniform(EFFECT_SIZE_MIN, EFFECT_SIZE_MAX)
        treatment_mean = control_mean + effect_size * control_mean * 0.1  # Relative effect
        
        control_std = random.uniform(CONTINUOUS_STD_MIN, CONTINUOUS_STD_MAX)
        treatment_std = control_std * random.uniform(0.8, 1.2)
        
        record = generate_continuous_outcome(
            n=idx,
            control_size=control_sizes[idx],
            treatment_size=treatment_sizes[idx],
            control_mean=control_mean,
            treatment_mean=treatment_mean,
            control_std=control_std,
            treatment_std=treatment_std,
            inject_inconsistency=inject_inconsistency
        )
        records.append(record)
    
    ground_truth["outcome_types"]["continuous"] = {
        "count": continuous_count,
        "inconsistent_count": continuous_inconsistent,
        "consistent_count": continuous_count - continuous_inconsistent
    }
    
    total_inconsistent = binary_inconsistent + continuous_inconsistent
    ground_truth["total_inconsistent"] = total_inconsistent
    ground_truth["total_consistent"] = total_records - total_inconsistent
    
    logger.info(f"Generated {total_records} synthetic records")
    logger.info(f"Binary: {binary_count}, Continuous: {continuous_count}")
    logger.info(f"Inconsistent: {total_inconsistent} ({total_inconsistent/total_records*100:.2f}%)")
    
    return records, ground_truth

def write_csv_output(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Write synthetic records to CSV file."""
    if not records:
        raise ValueError("No records to write")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Define CSV fields
    fieldnames = list(records[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    
    logger.info(f"Wrote {len(records)} records to {output_path}")

def write_json_output(ground_truth: Dict[str, Any], output_path: Path) -> None:
    """Write ground truth metadata to JSON file."""
    if not ground_truth:
        raise ValueError("No ground truth data to write")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(ground_truth, f, indent=2)
    
    logger.info(f"Wrote ground truth to {output_path}")

def verify_outcome_types(records: List[Dict[str, Any]]) -> Tuple[int, int]:
    """
    Verify that both binary and continuous outcome types are present.
    
    Returns:
        Tuple of (binary_count, continuous_count)
    """
    binary_count = sum(1 for r in records if r.get("outcome_type") == "binary")
    continuous_count = sum(1 for r in records if r.get("outcome_type") == "continuous")
    
    logger.info(f"Verification: Binary={binary_count}, Continuous={continuous_count}")
    
    if binary_count == 0:
        raise ValueError("No binary outcome records found")
    if continuous_count == 0:
        raise ValueError("No continuous outcome records found")
    
    return binary_count, continuous_count

def main() -> None:
    """Main entry point for synthetic dataset generation."""
    # Define output paths
    base_dir = Path("data/synthetic")
    csv_path = base_dir / "synthetic_validation.csv"
    json_path = base_dir / "synthetic_ground_truth.json"
    
    try:
        # Generate dataset
        records, ground_truth = generate_synthetic_dataset(
            total_records=TOTAL_RECORDS,
            inconsistency_rate=0.15
        )
        
        # Write outputs
        write_csv_output(records, csv_path)
        write_json_output(ground_truth, json_path)
        
        # Verify outcome types
        binary_count, continuous_count = verify_outcome_types(records)
        
        # Final validation
        if binary_count + continuous_count < TOTAL_RECORDS:
            raise ValueError(f"Generated {binary_count + continuous_count} records, expected {TOTAL_RECORDS}")
        
        logger.info("Synthetic dataset generation completed successfully")
        logger.info(f"Output files: {csv_path}, {json_path}")
        
    except Exception as e:
        logger.error(f"Failed to generate synthetic dataset: {e}")
        raise

if __name__ == "__main__":
    main()
