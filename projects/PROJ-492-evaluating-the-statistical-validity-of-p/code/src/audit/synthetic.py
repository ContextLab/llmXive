"""
Synthetic dataset generator for A/B test validation (FR-030).
Generates at least 10,000 simulated summaries with both binary and continuous outcomes.
"""
import csv
import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from scipy import stats

from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.models.data_models import ABTestSummary

# Initialize logger
logger = get_default_logger()


def set_all_seeds(seed: int = SEED) -> None:
    """Set seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    set_rng_seed(seed)


def generate_sample_sizes(n: int, min_n: int = 100, max_n: int = 10000) -> Tuple[List[int], List[int]]:
    """
    Generate sample sizes for control and treatment groups.
    Returns two lists of length n.
    """
    sizes = []
    for _ in range(n):
        n_control = random.randint(min_n, max_n)
        # Treatment size is usually similar, with some variation
        n_treatment = random.randint(int(n_control * 0.8), int(n_control * 1.2))
        sizes.append((n_control, n_treatment))
    return sizes


def generate_binary_outcome(
    n: int,
    baseline_rate: float = 0.1,
    effect_size: Optional[float] = None,
    inject_inconsistency: bool = False
) -> List[Dict[str, Any]]:
    """
    Generate synthetic binary outcome data.
    Returns a list of dictionaries with keys:
    - n_control, n_treatment, conversions_control, conversions_treatment,
      reported_p_value, reported_effect_size, outcome_type
    """
    results = []
    for _ in range(n):
        n_control, n_treatment = random.choice(generate_sample_sizes(1))[0]
        
        # True baseline and treatment rates
        true_baseline = baseline_rate
        if effect_size is not None:
            true_treatment = true_baseline + effect_size
        else:
            # Random effect size between -0.05 and 0.15
            true_treatment = true_baseline + random.uniform(-0.05, 0.15)
        
        true_treatment = max(0.01, min(0.99, true_treatment))
        
        # Generate actual conversions
        conv_control = np.random.binomial(n_control, true_baseline)
        conv_treatment = np.random.binomial(n_treatment, true_treatment)
        
        # Calculate true p-value using two-proportion z-test
        p_val, effect = stats.proportions_ztest(
            [conv_control, conv_treatment],
            [n_control, n_treatment]
        )
        
        reported_p = p_val
        reported_effect = effect
        
        if inject_inconsistency:
            # Introduce a discrepancy between reported and calculated
            # Shift p-value by a random amount (up to 0.1 absolute difference)
            shift = random.uniform(-0.1, 0.1)
            reported_p = max(0.0, min(1.0, p_val + shift))
            # Slightly adjust effect size too
            reported_effect = effect + random.uniform(-0.02, 0.02)
        
        results.append({
            "n_control": int(n_control),
            "n_treatment": int(n_treatment),
            "conversions_control": int(conv_control),
            "conversions_treatment": int(conv_treatment),
            "reported_p_value": float(reported_p),
            "reported_effect_size": float(reported_effect),
            "outcome_type": "binary",
            "domain": random.choice(["tech", "health", "finance", "education", "retail"]),
            "year": random.randint(2018, 2024)
        })
    
    return results


def generate_continuous_outcome(
    n: int,
    baseline_mean: float = 50.0,
    baseline_std: float = 15.0,
    effect_size: Optional[float] = None,
    inject_inconsistency: bool = False
) -> List[Dict[str, Any]]:
    """
    Generate synthetic continuous outcome data.
    Returns a list of dictionaries with keys:
    - n_control, n_treatment, mean_control, mean_treatment, std_control, std_treatment,
      reported_p_value, reported_effect_size, outcome_type
    """
    results = []
    for _ in range(n):
        n_control, n_treatment = random.choice(generate_sample_sizes(1))[0]
        
        # True parameters
        true_baseline_mean = baseline_mean
        if effect_size is not None:
            true_treatment_mean = true_baseline_mean + effect_size
        else:
            # Random effect size between -5 and 10
            true_treatment_mean = true_baseline_mean + random.uniform(-5, 10)
        
        true_std = baseline_std * random.uniform(0.8, 1.2)
        
        # Generate actual data points (simulated)
        data_control = np.random.normal(true_baseline_mean, true_std, n_control)
        data_treatment = np.random.normal(true_treatment_mean, true_std, n_treatment)
        
        # Calculate true statistics
        mean_control = np.mean(data_control)
        mean_treatment = np.mean(data_treatment)
        std_control = np.std(data_control, ddof=1)
        std_treatment = np.std(data_treatment, ddof=1)
        
        # Calculate true p-value using Welch's t-test
        t_stat, true_p = stats.ttest_ind(data_control, data_treatment, equal_var=False)
        # Cohen's d
        pooled_std = np.sqrt((std_control**2 + std_treatment**2) / 2)
        true_effect = (mean_treatment - mean_control) / pooled_std if pooled_std > 0 else 0.0
        
        reported_p = true_p
        reported_effect = true_effect
        
        if inject_inconsistency:
            # Introduce discrepancy
            shift = random.uniform(-0.1, 0.1)
            reported_p = max(0.0, min(1.0, true_p + shift))
            reported_effect = true_effect + random.uniform(-0.05, 0.05)
        
        results.append({
            "n_control": int(n_control),
            "n_treatment": int(n_treatment),
            "mean_control": float(mean_control),
            "mean_treatment": float(mean_treatment),
            "std_control": float(std_control),
            "std_treatment": float(std_treatment),
            "reported_p_value": float(reported_p),
            "reported_effect_size": float(reported_effect),
            "outcome_type": "continuous",
            "domain": random.choice(["tech", "health", "finance", "education", "retail"]),
            "year": random.randint(2018, 2024)
        })
    
    return results


def generate_synthetic_dataset(
    total_records: int = 10000,
    binary_ratio: float = 0.5,
    inject_inconsistency_rate: float = 0.2
) -> List[Dict[str, Any]]:
    """
    Generate a synthetic dataset with mixed binary and continuous outcomes.
    
    Args:
        total_records: Total number of records to generate (minimum 10000)
        binary_ratio: Proportion of binary outcomes (0.0 to 1.0)
        inject_inconsistency_rate: Proportion of records with intentional inconsistencies
    
    Returns:
        List of synthetic summary records
    """
    if total_records < 10000:
        logger.warning(f"Requested {total_records} records, but minimum is 10000. Adjusting to 10000.")
        total_records = 10000
    
    set_all_seeds()
    
    n_binary = int(total_records * binary_ratio)
    n_continuous = total_records - n_binary
    
    # Ensure both types are present
    if n_binary == 0:
        n_binary = 1
        n_continuous = total_records - 1
    if n_continuous == 0:
        n_continuous = 1
        n_binary = total_records - 1
    
    logger.info(f"Generating {n_binary} binary and {n_continuous} continuous records.")
    
    # Generate binary outcomes
    binary_count_with_inconsistency = int(n_binary * inject_inconsistency_rate)
    binary_count_consistent = n_binary - binary_count_with_inconsistency
    
    binary_data = []
    binary_data.extend(generate_binary_outcome(binary_count_consistent, inject_inconsistency=False))
    binary_data.extend(generate_binary_outcome(binary_count_with_inconsistency, inject_inconsistency=True))
    
    # Generate continuous outcomes
    continuous_count_with_inconsistency = int(n_continuous * inject_inconsistency_rate)
    continuous_count_consistent = n_continuous - continuous_count_with_inconsistency
    
    continuous_data = []
    continuous_data.extend(generate_continuous_outcome(continuous_count_consistent, inject_inconsistency=False))
    continuous_data.extend(generate_continuous_outcome(continuous_count_with_inconsistency, inject_inconsistency=True))
    
    # Combine and shuffle
    all_data = binary_data + continuous_data
    random.shuffle(all_data)
    
    return all_data


def verify_outcome_types(data: List[Dict[str, Any]]) -> Tuple[bool, Dict[str, int]]:
    """
    Verify that both binary and continuous outcome types are present.
    
    Returns:
        Tuple of (success, counts_dict)
    """
    counts = {"binary": 0, "continuous": 0}
    for record in data:
        outcome_type = record.get("outcome_type")
        if outcome_type in counts:
            counts[outcome_type] += 1
    
    success = counts["binary"] > 0 and counts["continuous"] > 0
    logger.info(f"Outcome type verification: {counts}")
    if not success:
        logger.error(f"Missing outcome types. Binary: {counts['binary']}, Continuous: {counts['continuous']}")
    
    return success, counts


def write_csv_output(data: List[Dict[str, Any]], output_path: Path) -> None:
    """Write synthetic data to CSV file."""
    if not data:
        raise ValueError("No data to write.")
    
    fieldnames = list(data[0].keys())
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    logger.info(f"Wrote {len(data)} records to {output_path}")


def write_json_output(data: List[Dict[str, Any]], output_path: Path) -> None:
    """Write synthetic data to JSON file."""
    if not data:
        raise ValueError("No data to write.")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Wrote {len(data)} records to {output_path}")


def write_metadata(counts: Dict[str, int], total: int, output_path: Path) -> None:
    """Write metadata about the generated dataset."""
    metadata = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_records": total,
        "outcome_counts": counts,
        "has_both_types": counts["binary"] > 0 and counts["continuous"] > 0
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Wrote metadata to {output_path}")


def main() -> int:
    """Main entry point for synthetic dataset generation."""
    logger.info("Starting synthetic dataset generation (T026).")
    
    # Configuration
    total_records = 10000
    binary_ratio = 0.5
    inconsistency_rate = 0.2
    
    # Output paths
    base_dir = Path("data")
    csv_path = base_dir / "synthetic" / "synthetic_summaries.csv"
    json_path = base_dir / "synthetic" / "synthetic_summaries.json"
    metadata_path = base_dir / "synthetic" / "synthetic_metadata.json"
    
    try:
        # Generate data
        data = generate_synthetic_dataset(
            total_records=total_records,
            binary_ratio=binary_ratio,
            inject_inconsistency_rate=inconsistency_rate
        )
        
        # Verify outcome types
        success, counts = verify_outcome_types(data)
        if not success:
            logger.error("Verification failed: missing outcome types.")
            return 1
        
        if len(data) < 10000:
            logger.error(f"Generated {len(data)} records, but required at least 10000.")
            return 1
        
        # Write outputs
        write_csv_output(data, csv_path)
        write_json_output(data, json_path)
        write_metadata(counts, len(data), metadata_path)
        
        logger.info(f"Successfully generated {len(data)} synthetic records.")
        logger.info(f"Binary: {counts['binary']}, Continuous: {counts['continuous']}")
        
        return 0
    
    except Exception as e:
        logger.error(f"Error generating synthetic dataset: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
