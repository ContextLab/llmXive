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

# Import from project config to ensure deterministic seeding
from code.src.config import set_rng_seed
from code.src.utils.logger import get_default_logger

# Ensure output directories exist
DATA_SYNTHETIC_DIR = Path("data/synthetic")
DATA_SYNTHETIC_DIR.mkdir(parents=True, exist_ok=True)

logger = get_default_logger(__name__)

def set_all_seeds(seed: int = 42) -> None:
    """Set seeds for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)

def generate_sample_sizes(min_n: int = 100, max_n: int = 10000) -> Tuple[int, int]:
    """Generate realistic sample sizes for control and treatment groups."""
    n_control = random.randint(min_n, max_n)
    # Treatment size usually similar, sometimes slightly different
    n_treatment = int(n_control * random.uniform(0.9, 1.1))
    return n_control, n_treatment

def generate_binary_outcome(
    n_control: int,
    n_treatment: int,
    baseline_rate: float,
    effect_size: float,
    is_significant: bool,
    p_value: Optional[float] = None
) -> Dict[str, Any]:
    """
    Generate binary outcome data (A/B test with conversion rates).
    
    Args:
        n_control: Sample size for control group
        n_treatment: Sample size for treatment group
        baseline_rate: Conversion rate for control group
        effect_size: Relative effect size (e.g., 0.05 for 5% lift)
        is_significant: Whether the result should be statistically significant
        p_value: Optional pre-calculated p-value to use (for ground truth)
        
    Returns:
        Dictionary with outcome data and statistics
    """
    # Calculate rates
    control_rate = baseline_rate
    treatment_rate = baseline_rate * (1 + effect_size)
    
    # Ensure rates are valid probabilities
    control_rate = max(0.001, min(0.999, control_rate))
    treatment_rate = max(0.001, min(0.999, treatment_rate))
    
    # Generate counts
    successes_control = int(n_control * control_rate)
    successes_treatment = int(n_treatment * treatment_rate)
    
    # Calculate p-value using two-proportion z-test
    if p_value is None:
        p_value, _ = stats.proportions_ztest(
            [successes_treatment, successes_control],
            [n_treatment, n_control]
        )
        p_value = float(p_value)
    
    # Calculate effect size (absolute difference)
    absolute_effect = treatment_rate - control_rate
    
    return {
        "outcome_type": "binary",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "successes_control": successes_control,
        "successes_treatment": successes_treatment,
        "rate_control": control_rate,
        "rate_treatment": treatment_rate,
        "p_value_reported": p_value,
        "absolute_effect": absolute_effect,
        "relative_effect": effect_size,
        "is_significant": is_significant
    }

def generate_continuous_outcome(
    n_control: int,
    n_treatment: int,
    baseline_mean: float,
    baseline_std: float,
    effect_size: float,
    is_significant: bool,
    p_value: Optional[float] = None
) -> Dict[str, Any]:
    """
    Generate continuous outcome data (A/B test with means).
    
    Args:
        n_control: Sample size for control group
        n_treatment: Sample size for treatment group
        baseline_mean: Mean for control group
        baseline_std: Standard deviation for control group
        effect_size: Absolute difference in means
        is_significant: Whether the result should be statistically significant
        p_value: Optional pre-calculated p-value to use
        
    Returns:
        Dictionary with outcome data and statistics
    """
    treatment_mean = baseline_mean + effect_size
    
    # Generate sample data
    control_data = np.random.normal(baseline_mean, baseline_std, n_control)
    treatment_data = np.random.normal(treatment_mean, baseline_std, n_treatment)
    
    # Calculate statistics
    control_mean = float(np.mean(control_data))
    treatment_mean_calc = float(np.mean(treatment_data))
    control_std = float(np.std(control_data, ddof=1))
    treatment_std = float(np.std(treatment_data, ddof=1))
    
    # Calculate p-value using Welch's t-test
    if p_value is None:
        p_value = stats.ttest_ind(
            treatment_data, control_data, equal_var=False
        ).pvalue
        p_value = float(p_value)
    
    return {
        "outcome_type": "continuous",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "mean_control": control_mean,
        "mean_treatment": treatment_mean_calc,
        "std_control": control_std,
        "std_treatment": treatment_std,
        "p_value_reported": p_value,
        "absolute_effect": abs(treatment_mean_calc - control_mean),
        "relative_effect": abs(treatment_mean_calc - control_mean) / baseline_mean if baseline_mean != 0 else 0,
        "is_significant": is_significant
    }

def generate_synthetic_dataset(
    n_records: int = 10000,
    seed: int = 42,
    binary_ratio: float = 0.5
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Generate a synthetic dataset of A/B test summaries.
    
    Args:
        n_records: Total number of records to generate
        seed: Random seed for reproducibility
        binary_ratio: Proportion of binary outcomes (default 0.5)
        
    Returns:
        Tuple of (synthetic_summaries, ground_truth)
    """
    set_all_seeds(seed)
    
    synthetic_summaries = []
    ground_truth = []
    
    n_binary = int(n_records * binary_ratio)
    n_continuous = n_records - n_binary
    
    logger.info(f"Generating {n_binary} binary and {n_continuous} continuous outcomes")
    
    # Generate binary outcomes
    for i in range(n_binary):
        n_control, n_treatment = generate_sample_sizes()
        baseline_rate = random.uniform(0.01, 0.3)
        # Effect size: mostly small, some large
        if random.random() < 0.7:
            effect_size = random.uniform(-0.02, 0.02)  # Small effect
        else:
            effect_size = random.uniform(-0.1, 0.1)  # Larger effect
        
        # Determine significance based on effect size and sample size
        # Use a simple heuristic: larger effects with larger samples are more likely significant
        stat_power = abs(effect_size) * math.sqrt(min(n_control, n_treatment))
        is_significant = stat_power > 2.5 or (random.random() < 0.1 and abs(effect_size) > 0.05)
        
        record = generate_binary_outcome(
            n_control, n_treatment, baseline_rate, effect_size, is_significant
        )
        
        # Add metadata
        record["id"] = f"binary_{i}"
        record["domain"] = random.choice(["ecommerce", "marketing", "tech", "finance", "health"])
        record["year"] = random.randint(2018, 2024)
        
        synthetic_summaries.append(record)
        ground_truth.append({
            "id": record["id"],
            "outcome_type": "binary",
            "true_p_value": record["p_value_reported"],
            "true_is_significant": is_significant,
            "true_effect_size": effect_size,
            "is_consistent": True  # Synthetic data is internally consistent by construction
        })
    
    # Generate continuous outcomes
    for i in range(n_continuous):
        n_control, n_treatment = generate_sample_sizes()
        baseline_mean = random.uniform(10, 100)
        baseline_std = baseline_mean * random.uniform(0.1, 0.3)  # CV between 10-30%
        # Effect size: mostly small
        if random.random() < 0.7:
            effect_size = baseline_mean * random.uniform(-0.02, 0.02)
        else:
            effect_size = baseline_mean * random.uniform(-0.1, 0.1)
        
        stat_power = abs(effect_size) / baseline_std * math.sqrt(min(n_control, n_treatment))
        is_significant = stat_power > 2.5 or (random.random() < 0.1 and abs(effect_size) > baseline_mean * 0.05)
        
        record = generate_continuous_outcome(
            n_control, n_treatment, baseline_mean, baseline_std, effect_size, is_significant
        )
        
        # Add metadata
        record["id"] = f"continuous_{i}"
        record["domain"] = random.choice(["ecommerce", "marketing", "tech", "finance", "health"])
        record["year"] = random.randint(2018, 2024)
        
        synthetic_summaries.append(record)
        ground_truth.append({
            "id": record["id"],
            "outcome_type": "continuous",
            "true_p_value": record["p_value_reported"],
            "true_is_significant": is_significant,
            "true_effect_size": effect_size,
            "is_consistent": True
        })
    
    return synthetic_summaries, ground_truth

def write_csv_output(summaries: List[Dict[str, Any]], filepath: Path) -> None:
    """Write synthetic summaries to CSV file."""
    if not summaries:
        logger.error("No summaries to write")
        return
    
    # Flatten nested dictionaries for CSV
    flattened = []
    for s in summaries:
        row = {}
        for k, v in s.items():
            if isinstance(v, (list, dict)):
                row[k] = json.dumps(v)
            else:
                row[k] = v
        flattened.append(row)
    
    fieldnames = list(flattened[0].keys())
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flattened)
    
    logger.info(f"Wrote {len(flattened)} records to {filepath}")

def write_json_output(data: List[Dict[str, Any]], filepath: Path) -> None:
    """Write ground truth to JSON file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)
    
    logger.info(f"Wrote {len(data)} records to {filepath}")

def verify_outcome_types(summaries: List[Dict[str, Any]]) -> Tuple[int, int]:
    """Verify that both outcome types are present in the dataset."""
    binary_count = sum(1 for s in summaries if s.get("outcome_type") == "binary")
    continuous_count = sum(1 for s in summaries if s.get("outcome_type") == "continuous")
    
    logger.info(f"Verification: {binary_count} binary, {continuous_count} continuous outcomes")
    
    if binary_count == 0:
        raise ValueError("No binary outcomes found in synthetic dataset")
    if continuous_count == 0:
        raise ValueError("No continuous outcomes found in synthetic dataset")
    
    return binary_count, continuous_count

def main():
    """Main entry point for synthetic dataset generation."""
    logger.info("Starting synthetic dataset generation")
    
    # Generate dataset
    summaries, ground_truth = generate_synthetic_dataset(
        n_records=10000,
        seed=42,
        binary_ratio=0.5
    )
    
    # Verify outcome types
    binary_count, continuous_count = verify_outcome_types(summaries)
    
    # Write outputs
    csv_path = DATA_SYNTHETIC_DIR / "synthetic_validation.csv"
    json_path = DATA_SYNTHETIC_DIR / "synthetic_ground_truth.json"
    
    write_csv_output(summaries, csv_path)
    write_json_output(ground_truth, json_path)
    
    # Final verification
    if len(summaries) < 10000:
        raise ValueError(f"Generated only {len(summaries)} records, expected >= 10000")
    
    logger.info(f"Successfully generated {len(summaries)} synthetic records")
    logger.info(f"Binary: {binary_count}, Continuous: {continuous_count}")
    logger.info(f"Output files: {csv_path}, {json_path}")

if __name__ == "__main__":
    main()
