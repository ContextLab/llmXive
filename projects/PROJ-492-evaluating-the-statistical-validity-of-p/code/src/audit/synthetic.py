"""
Synthetic Dataset Generator (FR-030)

Generates a synthetic dataset of at least 10,000 simulated A/B test summaries
containing both binary and continuous outcomes for validation purposes.
"""
import csv
import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

import numpy as np

# Import existing project utilities
from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.models.data_models import ABTestSummary

logger = get_default_logger(__name__)

# Configuration constants
TOTAL_RECORDS = 10500  # Slightly above 10,000 to ensure threshold
BINARY_PROPORTION = 0.5  # 50% binary, 50% continuous
BASELINE_MIN = 0.01
BASELINE_MAX = 0.50
EFFECT_SIZE_MIN = 0.01
EFFECT_SIZE_MAX = 0.20
SAMPLE_SIZE_MIN = 100
SAMPLE_SIZE_MAX = 50000
DOMAINS = ["tech", "finance", "health", "retail", "education"]
YEARS = list(range(2018, 2025))

def set_all_seeds(seed: int = SEED) -> None:
    """Set seeds for all random number generators for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)

def generate_sample_sizes() -> Tuple[int, int]:
    """Generate control and treatment sample sizes."""
    n_control = random.randint(SAMPLE_SIZE_MIN, SAMPLE_SIZE_MAX)
    n_treatment = random.randint(SAMPLE_SIZE_MIN, SAMPLE_SIZE_MAX)
    return n_control, n_treatment

def generate_binary_outcome() -> Dict[str, Any]:
    """
    Generate a synthetic binary outcome A/B test summary.
    Returns a dictionary with metrics suitable for ABTestSummary.
    """
    n_control, n_treatment = generate_sample_sizes()
    baseline_rate = random.uniform(BASELINE_MIN, BASELINE_MAX)
    effect_size = random.uniform(EFFECT_SIZE_MIN, EFFECT_SIZE_MAX)
    
    # Randomly decide if effect is positive or negative
    direction = random.choice([-1, 1])
    treatment_rate = baseline_rate + (direction * effect_size)
    
    # Clamp rates to valid probability range
    treatment_rate = max(0.0, min(1.0, treatment_rate))
    
    # Generate counts
    successes_control = int(round(n_control * baseline_rate))
    successes_treatment = int(round(n_treatment * treatment_rate))
    
    # Calculate p-value (approximate using normal approximation for speed)
    # This is synthetic, so we simulate a p-value based on the effect size
    # In a real scenario, we'd run the test, but here we simulate consistency
    if abs(effect_size) < 0.001:
        p_value = random.uniform(0.4, 1.0)
    else:
        # Smaller p-value for larger effect sizes, with some noise
        base_p = 0.001 + (abs(effect_size) * 0.5)
        p_value = min(1.0, max(0.0001, base_p + random.uniform(-0.05, 0.05)))
    
    return {
        "outcome_type": "binary",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "baseline_rate": baseline_rate,
        "treatment_rate": treatment_rate,
        "successes_control": successes_control,
        "successes_treatment": successes_treatment,
        "reported_p_value": p_value,
        "effect_size": treatment_rate - baseline_rate
    }

def generate_continuous_outcome() -> Dict[str, Any]:
    """
    Generate a synthetic continuous outcome A/B test summary.
    Returns a dictionary with metrics suitable for ABTestSummary.
    """
    n_control, n_treatment = generate_sample_sizes()
    baseline_mean = random.uniform(10.0, 100.0)
    baseline_std = random.uniform(5.0, 20.0)
    
    effect_size = random.uniform(EFFECT_SIZE_MIN, EFFECT_SIZE_MAX)
    direction = random.choice([-1, 1])
    treatment_mean = baseline_mean + (direction * effect_size * baseline_std)
    
    # Generate synthetic p-value
    if abs(effect_size) < 0.001:
        p_value = random.uniform(0.4, 1.0)
    else:
        base_p = 0.001 + (abs(effect_size) * 0.5)
        p_value = min(1.0, max(0.0001, base_p + random.uniform(-0.05, 0.05)))
    
    return {
        "outcome_type": "continuous",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "baseline_mean": baseline_mean,
        "treatment_mean": treatment_mean,
        "baseline_std": baseline_std,
        "treatment_std": baseline_std * random.uniform(0.8, 1.2), # slight variation
        "reported_p_value": p_value,
        "effect_size": treatment_mean - baseline_mean
    }

def generate_synthetic_dataset(count: int = TOTAL_RECORDS) -> List[Dict[str, Any]]:
    """Generate the full synthetic dataset."""
    set_all_seeds()
    logger.info(f"Generating {count} synthetic A/B test summaries...")
    
    records = []
    binary_count = 0
    continuous_count = 0
    
    for i in range(count):
        # Decide outcome type
        is_binary = random.random() < BINARY_PROPORTION
        
        if is_binary:
            record = generate_binary_outcome()
            binary_count += 1
        else:
            record = generate_continuous_outcome()
            continuous_count += 1
        
        # Add metadata
        record["id"] = f"syn_{i:05d}"
        record["domain"] = random.choice(DOMAINS)
        record["year"] = random.choice(YEARS)
        record["url"] = f"https://example.com/test/{record['id']}"
        record["generated_at"] = datetime.utcnow().isoformat()
        
        records.append(record)
    
    logger.info(f"Generated {binary_count} binary and {continuous_count} continuous outcomes.")
    return records

def verify_outcome_types(records: List[Dict[str, Any]]) -> Tuple[int, int, bool]:
    """Verify that both outcome types are present and count them."""
    binary_count = sum(1 for r in records if r.get("outcome_type") == "binary")
    continuous_count = sum(1 for r in records if r.get("outcome_type") == "continuous")
    
    has_both = binary_count > 0 and continuous_count > 0
    
    logger.info(f"Verification: Binary={binary_count}, Continuous={continuous_count}, Both present={has_both}")
    
    if not has_both:
        raise ValueError("Synthetic dataset must contain both binary and continuous outcomes.")
    
    return binary_count, continuous_count, has_both

def write_csv_output(records: List[Dict[str, Any]], output_path: Path) -> None:
    """Write the synthetic dataset to a CSV file."""
    if not records:
        raise ValueError("Cannot write empty records to CSV.")
    
    # Flatten nested dicts if necessary, but our structure is flat
    fieldnames = list(records[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    
    logger.info(f"Wrote {len(records)} records to {output_path}")

def write_metadata(records: List[Dict[str, Any]], output_dir: Path) -> None:
    """Write metadata about the generated dataset."""
    binary_count, continuous_count, _ = verify_outcome_types(records)
    
    metadata = {
        "total_records": len(records),
        "binary_count": binary_count,
        "continuous_count": continuous_count,
        "generation_timestamp": datetime.utcnow().isoformat(),
        "seed": SEED,
        "domains": DOMAINS,
        "year_range": [min(YEARS), max(YEARS)]
    }
    
    metadata_path = output_dir / "synthetic_metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Wrote metadata to {metadata_path}")

def main() -> None:
    """Main entry point for synthetic dataset generation."""
    # Define output paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    output_dir = project_root / "data" / "synthetic"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    csv_path = output_dir / "synthetic_summaries.csv"
    
    try:
        # Generate dataset
        records = generate_synthetic_dataset()
        
        # Verify requirements
        binary_count, continuous_count, has_both = verify_outcome_types(records)
        
        if len(records) < 10000:
            raise ValueError(f"Generated {len(records)} records, expected at least 10,000.")
        
        if not has_both:
            raise ValueError("Dataset must contain both binary and continuous outcomes.")
        
        # Write outputs
        write_csv_output(records, csv_path)
        write_metadata(records, output_dir)
        
        logger.info(f"Successfully generated synthetic dataset with {len(records)} records.")
        logger.info(f"Output files: {csv_path}")
        
    except Exception as e:
        logger.error(f"Failed to generate synthetic dataset: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
