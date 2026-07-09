"""
Synthetic Dataset Generator (FR-030)

Generates a synthetic corpus of A/B test summaries for validation purposes.
Outputs at least 10,000 simulated summaries with both binary and continuous outcomes.
"""
import csv
import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np

# Import from project API surface
from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.models.data_models import ABTestSummary

logger = get_default_logger()

# Constants
MIN_RECORDS = 10000
BINARY_RATIO = 0.5  # 50% binary, 50% continuous
DOMAINS = ["tech", "finance", "health", "retail", "media"]
YEARS = list(range(2018, 2025))


def set_all_seeds(seed: int = SEED) -> None:
    """Ensure deterministic behavior for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)


def generate_sample_sizes() -> Tuple[int, int]:
    """
    Generate realistic sample sizes for control and treatment groups.
    Returns (n_control, n_treatment).
    """
    # Sample sizes typically range from 100 to 50,000
    base_n = int(np.random.lognormal(mean=4.5, sigma=1.0))
    # Add some variation between groups
    n_control = max(100, base_n)
    n_treatment = max(100, int(base_n * np.random.uniform(0.8, 1.2)))
    return n_control, n_treatment


def generate_binary_outcome(
    n_control: int, n_treatment: int, baseline_rate: float, effect_size: float
) -> Dict[str, Any]:
    """
    Generate data for a binary outcome A/B test.
    Simulates conversions based on baseline and effect size.
    """
    # Apply effect size to treatment group
    treatment_rate = baseline_rate + effect_size
    treatment_rate = max(0.0, min(1.0, treatment_rate))

    # Simulate successes
    successes_control = int(np.random.binomial(n_control, baseline_rate))
    successes_treatment = int(np.random.binomial(n_treatment, treatment_rate))

    # Calculate observed rates
    rate_control = successes_control / n_control if n_control > 0 else 0.0
    rate_treatment = successes_treatment / n_treatment if n_treatment > 0 else 0.0

    # Calculate p-value (two-proportion z-test approximation)
    # Using scipy.stats would be ideal, but we simulate the p-value here
    # to avoid heavy dependencies in generation, using normal approx
    if n_control > 0 and n_treatment > 0:
        p_pooled = (successes_control + successes_treatment) / (n_control + n_treatment)
        if p_pooled > 0 and p_pooled < 1:
            se = np.sqrt(p_pooled * (1 - p_pooled) * (1/n_control + 1/n_treatment))
            z_stat = (rate_treatment - rate_control) / se if se > 0 else 0.0
            # Two-tailed p-value from standard normal
            p_value = 2 * (1 - 0.5 * (1 + np.math.erf(abs(z_stat) / np.sqrt(2))))
        else:
            p_value = 1.0
    else:
        p_value = 1.0

    return {
        "outcome_type": "binary",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "successes_control": successes_control,
        "successes_treatment": successes_treatment,
        "rate_control": rate_control,
        "rate_treatment": rate_treatment,
        "p_value": p_value,
        "effect_size": effect_size,
        "baseline_rate": baseline_rate
    }


def generate_continuous_outcome(
    n_control: int, n_treatment: int, baseline_mean: float, effect_size: float
) -> Dict[str, Any]:
    """
    Generate data for a continuous outcome A/B test.
    Simulates means and standard deviations.
    """
    # Standard deviation typically 10-50% of mean
    std_dev = baseline_mean * np.random.uniform(0.1, 0.5)
    if std_dev <= 0:
        std_dev = 1.0

    # Simulate means
    mean_control = baseline_mean
    mean_treatment = baseline_mean + effect_size

    # Generate synthetic data points to calculate stats (optional, but good for realism)
    # For efficiency, we calculate stats directly from distributions
    # We simulate a small sample to estimate variance if needed, but here we use known params
    
    # Calculate t-statistic (Welch's t-test approximation)
    se_diff = np.sqrt((std_dev**2 / n_control) + (std_dev**2 / n_treatment))
    t_stat = (mean_treatment - mean_control) / se_diff if se_diff > 0 else 0.0

    # Degrees of freedom approximation (Welch-Satterthwaite)
    df_num = (std_dev**2/n_control + std_dev**2/n_treatment)**2
    df_den = (std_dev**2/n_control)**2/(n_control-1) + (std_dev**2/n_treatment)**2/(n_treatment-1)
    df = df_num / df_den if df_den > 0 else n_control + n_treatment - 2

    # Approximate p-value from t-distribution
    # Using normal approx for large N, or t-distribution logic
    # Since we don't want to import scipy.stats here if possible, use normal approx for large N
    if df > 30:
        p_value = 2 * (1 - 0.5 * (1 + np.math.erf(abs(t_stat) / np.sqrt(2))))
    else:
        # Fallback: rough approximation for small df
        p_value = 2 * (1 - 0.5 * (1 + np.math.erf(abs(t_stat) / np.sqrt(2))))

    return {
        "outcome_type": "continuous",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "mean_control": mean_control,
        "mean_treatment": mean_treatment,
        "std_dev": std_dev,
        "p_value": p_value,
        "effect_size": effect_size,
        "baseline_mean": baseline_mean
    }


def generate_synthetic_dataset(
    num_records: int = MIN_RECORDS,
    output_dir: Path = Path("data/synthetic"),
    filename: str = "synthetic_summaries.csv"
) -> List[Dict[str, Any]]:
    """
    Generate the full synthetic dataset.
    Returns a list of dictionaries representing summaries.
    """
    set_all_seeds()
    
    output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    
    # Ensure we have both outcome types
    num_binary = int(num_records * BINARY_RATIO)
    num_continuous = num_records - num_binary

    logger.info(f"Generating {num_binary} binary and {num_continuous} continuous outcomes.")

    for i in range(num_binary):
        n_c, n_t = generate_sample_sizes()
        baseline = np.random.uniform(0.01, 0.20) # 1% to 20% conversion
        # Effect size: mostly small, some large
        if np.random.random() < 0.1:
            effect = np.random.choice([-1, 1]) * np.random.uniform(0.05, 0.15)
        else:
            effect = np.random.choice([-1, 1]) * np.random.uniform(0.001, 0.03)
        
        data = generate_binary_outcome(n_c, n_t, baseline, effect)
        data["id"] = f"synthetic_{i:05d}"
        data["domain"] = random.choice(DOMAINS)
        data["year"] = random.choice(YEARS)
        data["test_name"] = f"Test_{i}"
        records.append(data)

    for i in range(num_continuous):
        idx = num_binary + i
        n_c, n_t = generate_sample_sizes()
        baseline = np.random.uniform(10.0, 100.0) # e.g., time on site, revenue
        # Effect size: small shifts
        if np.random.random() < 0.1:
            effect = np.random.choice([-1, 1]) * np.random.uniform(5.0, 15.0)
        else:
            effect = np.random.choice([-1, 1]) * np.random.uniform(0.1, 2.0)

        data = generate_continuous_outcome(n_c, n_t, baseline, effect)
        data["id"] = f"synthetic_{idx:05d}"
        data["domain"] = random.choice(DOMAINS)
        data["year"] = random.choice(YEARS)
        data["test_name"] = f"Test_{idx}"
        records.append(data)

    # Shuffle to mix types
    random.shuffle(records)

    # Write to CSV
    output_path = output_dir / filename
    fieldnames = [
        "id", "outcome_type", "domain", "year", "test_name",
        "n_control", "n_treatment", "p_value", "effect_size",
        "baseline_rate", "rate_control", "rate_treatment",
        "successes_control", "successes_treatment",
        "baseline_mean", "mean_control", "mean_treatment", "std_dev"
    ]
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(records)

    logger.info(f"Generated {len(records)} synthetic records to {output_path}")
    return records


def verify_outcome_types(records: List[Dict[str, Any]]) -> Tuple[int, int]:
    """
    Verify that both binary and continuous outcome types are present.
    Returns (binary_count, continuous_count).
    """
    binary_count = sum(1 for r in records if r.get("outcome_type") == "binary")
    continuous_count = sum(1 for r in records if r.get("outcome_type") == "continuous")
    
    logger.info(f"Verification: Binary={binary_count}, Continuous={continuous_count}")
    
    if binary_count == 0:
        raise ValueError("No binary outcomes found in generated dataset.")
    if continuous_count == 0:
        raise ValueError("No continuous outcomes found in generated dataset.")
    if binary_count + continuous_count < MIN_RECORDS:
        raise ValueError(f"Total records {binary_count + continuous_count} < {MIN_RECORDS}")
        
    return binary_count, continuous_count


def write_metadata(output_dir: Path, records: List[Dict[str, Any]]) -> None:
    """Write metadata about the generated dataset."""
    metadata = {
        "generated_at": datetime.now().isoformat(),
        "total_records": len(records),
        "outcome_types": {
            "binary": sum(1 for r in records if r["outcome_type"] == "binary"),
            "continuous": sum(1 for r in records if r["outcome_type"] == "continuous")
        },
        "domains": list(set(r["domain"] for r in records)),
        "years": list(set(r["year"] for r in records)),
        "seed": SEED
    }
    
    metadata_path = output_dir / "synthetic_metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Metadata written to {metadata_path}")


def main() -> None:
    """Main entry point for synthetic dataset generation."""
    logger.info("Starting synthetic dataset generation (T026)...")
    
    output_dir = Path("data/synthetic")
    filename = "synthetic_summaries.csv"
    
    try:
        records = generate_synthetic_dataset(num_records=MIN_RECORDS, output_dir=output_dir, filename=filename)
        
        # Verify requirements
        b_count, c_count = verify_outcome_types(records)
        assert b_count > 0 and c_count > 0, "Missing outcome types"
        assert len(records) >= MIN_RECORDS, "Insufficient records"
        
        # Write metadata
        write_metadata(output_dir, records)
        
        logger.info("Synthetic dataset generation completed successfully.")
        
    except Exception as e:
        logger.error(f"Synthetic dataset generation failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
