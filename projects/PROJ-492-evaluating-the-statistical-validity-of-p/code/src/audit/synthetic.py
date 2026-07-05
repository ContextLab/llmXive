"""
Synthetic dataset generator for A/B test summaries.
Generates at least 10,000 simulated summaries with both binary and continuous outcomes.
Implements FR-030 requirements.
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

from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.models.data_models import ABTestSummary

# Initialize logger
logger: AuditLogger = get_default_logger(__name__)

def set_all_seeds(seed: int = SEED) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Random seeds set to {seed}")

def generate_sample_sizes(min_n: int = 100, max_n: int = 10000) -> Tuple[int, int]:
    """
    Generate realistic sample sizes for control and treatment groups.
    Returns (n_control, n_treatment).
    """
    # Sample sizes are typically in the hundreds to thousands for A/B tests
    n_control = random.randint(min_n, max_n)
    # Treatment group size is often similar to control, but can vary
    n_treatment = random.randint(int(n_control * 0.8), int(n_control * 1.2))
    return n_control, n_treatment

def generate_binary_outcome(
    n_control: int,
    n_treatment: int,
    baseline_rate: float,
    effect_size: float
) -> Dict[str, Any]:
    """
    Generate binary outcome data (conversion rates).
    
    Args:
        n_control: Sample size for control group
        n_treatment: Sample size for treatment group
        baseline_rate: Conversion rate for control group
        effect_size: Effect size (relative change in conversion rate)
    
    Returns:
        Dictionary with observed conversions and rates
    """
    # Calculate expected conversion rate for treatment
    treatment_rate = baseline_rate * (1 + effect_size)
    
    # Ensure rates are within valid bounds
    treatment_rate = max(0.0, min(1.0, treatment_rate))
    
    # Generate observed conversions (binomial distribution)
    conversions_control = np.random.binomial(n_control, baseline_rate)
    conversions_treatment = np.random.binomial(n_treatment, treatment_rate)
    
    # Calculate observed rates
    observed_rate_control = conversions_control / n_control
    observed_rate_treatment = conversions_treatment / n_treatment
    
    # Calculate p-value using two-proportion z-test
    # Pooled proportion
    pooled_p = (conversions_control + conversions_treatment) / (n_control + n_treatment)
    
    # Standard error
    se = math.sqrt(pooled_p * (1 - pooled_p) * (1/n_control + 1/n_treatment))
    
    # Z-statistic
    if se > 0:
        z_stat = (observed_rate_treatment - observed_rate_control) / se
        # Two-tailed p-value
        p_value = 2 * (1 - abs(np.random.normal(0, 1) > abs(z_stat)))
        # Use scipy for accurate p-value
        from scipy import stats
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    else:
        p_value = 1.0
    
    return {
        "n_control": n_control,
        "n_treatment": n_treatment,
        "conversions_control": int(conversions_control),
        "conversions_treatment": int(conversions_treatment),
        "rate_control": observed_rate_control,
        "rate_treatment": observed_rate_treatment,
        "effect_size": effect_size,
        "p_value": p_value,
        "outcome_type": "binary"
    }

def generate_continuous_outcome(
    n_control: int,
    n_treatment: int,
    baseline_mean: float,
    baseline_std: float,
    effect_size: float
) -> Dict[str, Any]:
    """
    Generate continuous outcome data (e.g., revenue per user).
    
    Args:
        n_control: Sample size for control group
        n_treatment: Sample size for treatment group
        baseline_mean: Mean for control group
        baseline_std: Standard deviation for control group
        effect_size: Effect size (absolute change in mean)
    
    Returns:
        Dictionary with observed means, standard deviations, and p-value
    """
    # Calculate expected mean for treatment
    treatment_mean = baseline_mean + effect_size
    
    # Generate sample data (normal distribution)
    # Ensure standard deviation is positive
    treatment_std = max(baseline_std * 0.8, baseline_std * 1.2)
    
    data_control = np.random.normal(baseline_mean, baseline_std, n_control)
    data_treatment = np.random.normal(treatment_mean, treatment_std, n_treatment)
    
    # Calculate observed statistics
    observed_mean_control = float(np.mean(data_control))
    observed_std_control = float(np.std(data_control, ddof=1))
    observed_mean_treatment = float(np.mean(data_treatment))
    observed_std_treatment = float(np.std(data_treatment, ddof=1))
    
    # Calculate Welch's t-test p-value
    from scipy import stats
    t_stat, p_value = stats.ttest_ind(
        data_control, 
        data_treatment, 
        equal_var=False
    )
    
    return {
        "n_control": n_control,
        "n_treatment": n_treatment,
        "mean_control": observed_mean_control,
        "mean_treatment": observed_mean_treatment,
        "std_control": observed_std_control,
        "std_treatment": observed_std_treatment,
        "effect_size": effect_size,
        "p_value": float(p_value),
        "outcome_type": "continuous"
    }

def generate_synthetic_dataset(
    total_records: int = 10000,
    binary_ratio: float = 0.5,
    output_dir: Path = None
) -> List[Dict[str, Any]]:
    """
    Generate a synthetic dataset of A/B test summaries.
    
    Args:
        total_records: Total number of records to generate (minimum 10,000)
        binary_ratio: Proportion of binary outcomes (default 0.5)
        output_dir: Directory to write output files (default: data/synthetic/)
    
    Returns:
        List of generated summary dictionaries
    """
    # Ensure minimum record count
    if total_records < 10000:
        logger.warning(f"Requested {total_records} records, using minimum 10,000")
        total_records = 10000
    
    if output_dir is None:
        output_dir = Path("data/synthetic")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Set seeds for reproducibility
    set_all_seeds()
    
    summaries = []
    num_binary = int(total_records * binary_ratio)
    num_continuous = total_records - num_binary
    
    logger.info(f"Generating {num_binary} binary and {num_continuous} continuous outcomes")
    
    # Generate binary outcomes
    for i in range(num_binary):
        # Randomize parameters for realism
        baseline_rate = random.uniform(0.01, 0.30)
        effect_size = random.choice([-0.1, -0.05, 0.0, 0.05, 0.1])
        n_control, n_treatment = generate_sample_sizes()
        
        outcome_data = generate_binary_outcome(
            n_control, n_treatment, baseline_rate, effect_size
        )
        
        # Create summary record
        summary = {
            "id": f"synthetic_binary_{i:05d}",
            "url": f"https://example.com/test/{i:05d}",
            "domain": random.choice(["tech", "ecommerce", "finance", "health", "media"]),
            "year": random.randint(2018, 2024),
            "outcome_type": "binary",
            "n_control": outcome_data["n_control"],
            "n_treatment": outcome_data["n_treatment"],
            "rate_control": outcome_data["rate_control"],
            "rate_treatment": outcome_data["rate_treatment"],
            "p_value": outcome_data["p_value"],
            "effect_size": outcome_data["effect_size"],
            "is_significant": outcome_data["p_value"] < 0.05,
            "generated_at": datetime.now().isoformat()
        }
        summaries.append(summary)
    
    # Generate continuous outcomes
    for i in range(num_continuous):
        # Randomize parameters for realism
        baseline_mean = random.uniform(10.0, 100.0)
        baseline_std = baseline_mean * random.uniform(0.3, 0.7)
        effect_size = random.choice([-5.0, -2.0, 0.0, 2.0, 5.0])
        n_control, n_treatment = generate_sample_sizes()
        
        outcome_data = generate_continuous_outcome(
            n_control, n_treatment, baseline_mean, baseline_std, effect_size
        )
        
        # Create summary record
        summary = {
            "id": f"synthetic_continuous_{i:05d}",
            "url": f"https://example.com/test/{num_binary + i:05d}",
            "domain": random.choice(["tech", "ecommerce", "finance", "health", "media"]),
            "year": random.randint(2018, 2024),
            "outcome_type": "continuous",
            "n_control": outcome_data["n_control"],
            "n_treatment": outcome_data["n_treatment"],
            "mean_control": outcome_data["mean_control"],
            "mean_treatment": outcome_data["mean_treatment"],
            "std_control": outcome_data["std_control"],
            "std_treatment": outcome_data["std_treatment"],
            "p_value": outcome_data["p_value"],
            "effect_size": outcome_data["effect_size"],
            "is_significant": outcome_data["p_value"] < 0.05,
            "generated_at": datetime.now().isoformat()
        }
        summaries.append(summary)
    
    # Write outputs
    write_csv_output(summaries, output_dir / "synthetic_summaries.csv")
    write_json_output(summaries, output_dir / "synthetic_summaries.json")
    
    # Verify outcome types
    verify_outcome_types(summaries)
    
    logger.info(f"Generated {len(summaries)} synthetic summaries")
    logger.info(f"Output files written to {output_dir}")
    
    return summaries

def write_csv_output(summaries: List[Dict[str, Any]], output_path: Path) -> None:
    """Write summaries to CSV file."""
    if not summaries:
        logger.warning("No summaries to write to CSV")
        return
    
    fieldnames = list(summaries[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)
    
    logger.info(f"CSV output written to {output_path}")

def write_json_output(summaries: List[Dict[str, Any]], output_path: Path) -> None:
    """Write summaries to JSON file."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summaries, f, indent=2, default=str)
    
    logger.info(f"JSON output written to {output_path}")

def verify_outcome_types(summaries: List[Dict[str, Any]]) -> None:
    """
    Verify that both binary and continuous outcomes are present.
    Raises an error if either type is missing.
    """
    binary_count = sum(1 for s in summaries if s["outcome_type"] == "binary")
    continuous_count = sum(1 for s in summaries if s["outcome_type"] == "continuous")
    
    logger.info(f"Verification: {binary_count} binary, {continuous_count} continuous")
    
    if binary_count == 0:
        raise ValueError("No binary outcomes generated - requirement violation")
    
    if continuous_count == 0:
        raise ValueError("No continuous outcomes generated - requirement violation")
    
    if len(summaries) < 10000:
        raise ValueError(f"Generated {len(summaries)} records, minimum 10,000 required")
    
    logger.info("Outcome type verification passed")

def main():
    """Main entry point for synthetic dataset generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate synthetic A/B test dataset")
    parser.add_argument(
        "--count", 
        type=int, 
        default=10000,
        help="Number of records to generate (default: 10000)"
    )
    parser.add_argument(
        "--binary-ratio",
        type=float,
        default=0.5,
        help="Proportion of binary outcomes (default: 0.5)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/synthetic",
        help="Output directory (default: data/synthetic)"
    )
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    
    try:
        summaries = generate_synthetic_dataset(
            total_records=args.count,
            binary_ratio=args.binary_ratio,
            output_dir=output_dir
        )
        
        print(f"Successfully generated {len(summaries)} synthetic summaries")
        print(f"Output files: {output_dir}/synthetic_summaries.csv, {output_dir}/synthetic_summaries.json")
        
    except Exception as e:
        logger.error(f"Failed to generate synthetic dataset: {e}")
        raise

if __name__ == "__main__":
    main()
