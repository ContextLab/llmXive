"""
Synthetic dataset generator for A/B test validity evaluation (FR-030).

Generates at least 10,000 simulated A/B test summaries with both binary and continuous outcomes.
Ensures statistical validity by using realistic distributions and parameters.
"""
import csv
import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np

from code.src.config import set_rng_seed, SEED
from code.src.utils.logger import get_default_logger, AuditLogger

# Initialize logger
logger = get_default_logger(__name__)
audit_logger = AuditLogger(logger)

def set_all_seeds(seed: int = SEED) -> None:
    """Set all random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    audit_logger.info(f"Seeds set to {seed}")

def generate_sample_sizes(n_min: int = 100, n_max: int = 10000) -> Tuple[int, int]:
    """
    Generate realistic sample sizes for control and treatment groups.
    Uses a log-normal distribution to mimic real-world A/B test sizes.
    """
    # Use log-normal to generate sizes that cluster around typical values
    mean_log = np.log(2000)
    std_log = 1.0
    
    n_control = int(np.clip(np.random.lognormal(mean_log, std_log), n_min, n_max))
    n_treatment = int(np.clip(np.random.lognormal(mean_log, std_log), n_min, n_max))
    
    return n_control, n_treatment

def generate_binary_outcome(
    n_control: int,
    n_treatment: int,
    baseline_rate: Optional[float] = None,
    effect_size: Optional[float] = None
) -> Dict[str, Any]:
    """
    Generate binary outcome data for an A/B test.
    
    Args:
        n_control: Sample size for control group
        n_treatment: Sample size for treatment group
        baseline_rate: Conversion rate for control group (default: random 0.05-0.30)
        effect_size: Relative effect size (default: random -0.2 to 0.5)
        
    Returns:
        Dictionary with n_control, n_treatment, successes_control, successes_treatment,
        rate_control, rate_treatment, effect_size, outcome_type
    """
    if baseline_rate is None:
        baseline_rate = random.uniform(0.05, 0.30)
    
    if effect_size is None:
        # Effect size: relative change in conversion rate
        effect_size = random.uniform(-0.2, 0.5)
    
    rate_control = baseline_rate
    rate_treatment = baseline_rate * (1 + effect_size)
    
    # Ensure rates are valid probabilities
    rate_treatment = np.clip(rate_treatment, 0.01, 0.99)
    
    # Generate successes
    successes_control = np.random.binomial(n_control, rate_control)
    successes_treatment = np.random.binomial(n_treatment, rate_treatment)
    
    return {
        "n_control": n_control,
        "n_treatment": n_treatment,
        "successes_control": int(successes_control),
        "successes_treatment": int(successes_treatment),
        "rate_control": round(rate_control, 6),
        "rate_treatment": round(rate_treatment, 6),
        "effect_size": round(effect_size, 6),
        "outcome_type": "binary",
        "test_type": "two_proportion_z"
    }

def generate_continuous_outcome(
    n_control: int,
    n_treatment: int,
    baseline_mean: Optional[float] = None,
    baseline_std: Optional[float] = None,
    effect_size: Optional[float] = None
) -> Dict[str, Any]:
    """
    Generate continuous outcome data for an A/B test.
    
    Args:
        n_control: Sample size for control group
        n_treatment: Sample size for treatment group
        baseline_mean: Mean for control group (default: random 10-100)
        baseline_std: Standard deviation for control group (default: random 5-20)
        effect_size: Cohen's d effect size (default: random -0.5 to 1.0)
        
    Returns:
        Dictionary with n_control, n_treatment, mean_control, mean_treatment,
        std_control, std_treatment, effect_size, outcome_type
    """
    if baseline_mean is None:
        baseline_mean = random.uniform(10, 100)
    
    if baseline_std is None:
        baseline_std = random.uniform(5, 20)
    
    if effect_size is None:
        # Cohen's d effect size
        effect_size = random.uniform(-0.5, 1.0)
    
    mean_control = baseline_mean
    std_control = baseline_std
    
    # Treatment mean based on effect size (Cohen's d)
    mean_treatment = mean_control + effect_size * std_control
    std_treatment = std_control * random.uniform(0.8, 1.2)  # Small variation in std
    
    # Ensure positive values for typical metrics
    mean_treatment = max(1.0, mean_treatment)
    std_treatment = max(0.1, std_treatment)
    
    return {
        "n_control": n_control,
        "n_treatment": n_treatment,
        "mean_control": round(mean_control, 4),
        "mean_treatment": round(mean_treatment, 4),
        "std_control": round(std_control, 4),
        "std_treatment": round(std_treatment, 4),
        "effect_size": round(effect_size, 6),
        "outcome_type": "continuous",
        "test_type": "welch_t"
    }

def generate_synthetic_dataset(
    n_records: int = 10000,
    binary_ratio: float = 0.5,
    output_dir: str = "data",
    filename: str = "synthetic_summaries.csv"
) -> Path:
    """
    Generate a synthetic dataset of A/B test summaries.
    
    Args:
        n_records: Total number of records to generate (minimum 10000)
        binary_ratio: Proportion of binary outcomes (default 0.5)
        output_dir: Output directory
        filename: Output filename
        
    Returns:
        Path to the generated CSV file
    """
    if n_records < 10000:
        logger.warning(f"Requested {n_records} records, minimum is 10000. Setting to 10000.")
        n_records = 10000
    
    set_all_seeds()
    
    output_path = Path(output_dir) / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    audit_logger.info(f"Generating {n_records} synthetic A/B test summaries")
    
    records = []
    binary_count = 0
    continuous_count = 0
    
    for i in range(n_records):
        # Determine outcome type
        if random.random() < binary_ratio:
            n_control, n_treatment = generate_sample_sizes()
            record = generate_binary_outcome(n_control, n_treatment)
            binary_count += 1
        else:
            n_control, n_treatment = generate_sample_sizes()
            record = generate_continuous_outcome(n_control, n_treatment)
            continuous_count += 1
        
        # Add metadata
        record["id"] = f"syn_{i:06d}"
        record["generated_at"] = datetime.now().isoformat()
        record["domain"] = random.choice([
            "e-commerce", "finance", "healthcare", "technology", "education"
        ])
        
        records.append(record)
    
    # Write to CSV
    fieldnames = [
        "id", "outcome_type", "test_type", "n_control", "n_treatment",
        "rate_control", "rate_treatment", "successes_control", "successes_treatment",
        "mean_control", "mean_treatment", "std_control", "std_treatment",
        "effect_size", "domain", "generated_at"
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            # Handle missing fields gracefully
            row = {k: record.get(k, "") for k in fieldnames}
            writer.writerow(row)
    
    audit_logger.info(f"Generated {binary_count} binary and {continuous_count} continuous outcomes")
    audit_logger.info(f"Output written to {output_path}")
    
    return output_path

def verify_outcome_types(
    filepath: Path,
    min_binary: int = 1000,
    min_continuous: int = 1000
) -> Tuple[bool, Dict[str, int]]:
    """
    Verify that the generated dataset contains both outcome types.
    
    Args:
        filepath: Path to the CSV file
        min_binary: Minimum required binary records
        min_continuous: Minimum required continuous records
        
    Returns:
        Tuple of (is_valid, counts_dict)
    """
    counts = {"binary": 0, "continuous": 0}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            outcome_type = row.get('outcome_type', '')
            if outcome_type in counts:
                counts[outcome_type] += 1
    
    is_valid = counts["binary"] >= min_binary and counts["continuous"] >= min_continuous
    
    audit_logger.info(f"Verification: {counts['binary']} binary, {counts['continuous']} continuous")
    
    if not is_valid:
        audit_logger.error(
            f"Verification failed: need at least {min_binary} binary and {min_continuous} continuous"
        )
    
    return is_valid, counts

def write_metadata(output_dir: str = "data", filename: str = "synthetic_metadata.json") -> Path:
    """Write metadata about the synthetic dataset generation."""
    metadata = {
        "generated_at": datetime.now().isoformat(),
        "total_records": 10000,
        "binary_ratio": 0.5,
        "random_seed": SEED,
        "description": "Synthetic A/B test summaries for validity evaluation",
        "outcome_types": ["binary", "continuous"],
        "test_types": ["two_proportion_z", "welch_t"]
    }
    
    metadata_path = Path(output_dir) / filename
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    audit_logger.info(f"Metadata written to {metadata_path}")
    return metadata_path

def main():
    """Main entry point for synthetic dataset generation."""
    output_dir = "data"
    csv_filename = "synthetic_summaries.csv"
    
    try:
        # Generate dataset
        csv_path = generate_synthetic_dataset(
            n_records=10000,
            binary_ratio=0.5,
            output_dir=output_dir,
            filename=csv_filename
        )
        
        # Verify outcome types
        is_valid, counts = verify_outcome_types(csv_path)
        
        if not is_valid:
            audit_logger.error("Synthetic dataset verification failed")
            return 1
        
        # Write metadata
        write_metadata(output_dir)
        
        audit_logger.info("Synthetic dataset generation completed successfully")
        return 0
        
    except Exception as e:
        audit_logger.error(f"Error generating synthetic dataset: {e}")
        raise

if __name__ == "__main__":
    import sys
    sys.exit(main())
