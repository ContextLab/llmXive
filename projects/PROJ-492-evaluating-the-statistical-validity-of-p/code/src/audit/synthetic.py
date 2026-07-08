"""
Synthetic dataset generator for A/B test validation.
Generates at least 10,000 simulated summaries with both binary and continuous outcomes.
"""
import csv
import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from scipy import stats

from code.src.config import SEED, set_rng_seed
from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.models.data_models import ABTestSummary

# Configuration
TOTAL_SUMMARIES = 10500  # > 10,000 as required
BINARY_RATIO = 0.5  # 50% binary, 50% continuous
OUTPUT_DIR = Path("data/synthetic")
SUMMARIES_FILE = OUTPUT_DIR / "synthetic_summaries.csv"
METADATA_FILE = OUTPUT_DIR / "synthetic_metadata.json"

logger = get_default_logger(__name__)

def set_all_seeds(seed: int = SEED) -> None:
    """Set all random seeds for reproducibility."""
    set_rng_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Seeds set to {seed}")

def generate_sample_sizes() -> Tuple[int, int]:
    """Generate realistic sample sizes for control and treatment groups."""
    # Sample sizes typically range from 100 to 10,000
    n_control = np.random.randint(100, 10000)
    n_treatment = np.random.randint(100, 10000)
    return int(n_control), int(n_treatment)

def generate_binary_outcome(
    n_control: int, n_treatment: int, baseline_rate: float, effect_size: float
) -> Dict[str, Any]:
    """
    Generate binary outcome data (conversion rates).
    Returns dict with success counts and rates.
    """
    # Control group
    control_successes = int(n_control * baseline_rate)
    # Treatment group with effect
    treatment_rate = baseline_rate * (1 + effect_size)
    treatment_rate = max(0.0, min(1.0, treatment_rate))  # Clamp to [0, 1]
    treatment_successes = int(n_treatment * treatment_rate)

    # Calculate p-value using two-proportion z-test
    try:
        stat, p_value = stats.proportions_ztest(
            [control_successes, treatment_successes],
            [n_control, n_treatment]
        )
    except Exception:
        p_value = 0.5  # Fallback for edge cases

    return {
        "outcome_type": "binary",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "control_successes": control_successes,
        "treatment_successes": treatment_successes,
        "baseline_rate": round(baseline_rate, 4),
        "treatment_rate": round(treatment_rate, 4),
        "effect_size": round(effect_size, 4),
        "p_value": round(p_value, 6),
        "statistic": round(stat, 4) if not np.isnan(stat) else 0.0
    }

def generate_continuous_outcome(
    n_control: int, n_treatment: int, baseline_mean: float, baseline_std: float,
    effect_size: float
) -> Dict[str, Any]:
    """
    Generate continuous outcome data (means and standard deviations).
    Returns dict with means, stds, and p-value.
    """
    # Generate sample data
    control_data = np.random.normal(baseline_mean, baseline_std, n_control)
    treatment_mean = baseline_mean * (1 + effect_size)
    treatment_data = np.random.normal(treatment_mean, baseline_std, n_treatment)

    control_mean = float(np.mean(control_data))
    treatment_mean_calc = float(np.mean(treatment_data))
    control_std = float(np.std(control_data, ddof=1))
    treatment_std = float(np.std(treatment_data, ddof=1))

    # Welch's t-test
    try:
        stat, p_value = stats.ttest_ind(
            control_data, treatment_data, equal_var=False
        )
    except Exception:
        p_value = 0.5
        stat = 0.0

    return {
        "outcome_type": "continuous",
        "n_control": n_control,
        "n_treatment": n_treatment,
        "control_mean": round(control_mean, 4),
        "treatment_mean": round(treatment_mean_calc, 4),
        "control_std": round(control_std, 4),
        "treatment_std": round(treatment_std, 4),
        "baseline_mean": round(baseline_mean, 4),
        "effect_size": round(effect_size, 4),
        "p_value": round(p_value, 6),
        "statistic": round(stat, 4) if not np.isnan(stat) else 0.0
    }

def generate_synthetic_dataset(
    total_count: int = TOTAL_SUMMARIES,
    binary_ratio: float = BINARY_RATIO
) -> List[Dict[str, Any]]:
    """
    Generate a synthetic dataset of A/B test summaries.
    Includes both binary and continuous outcomes.
    """
    set_all_seeds()
    summaries = []

    # Ensure we have enough of each type
    binary_count = int(total_count * binary_ratio)
    continuous_count = total_count - binary_count

    domains = ["tech", "finance", "health", "retail", "education"]
    years = list(range(2018, 2025))

    # Generate binary outcomes
    for i in range(binary_count):
        n_control, n_treatment = generate_sample_sizes()
        baseline_rate = np.random.uniform(0.05, 0.5)
        # Mix of positive, negative, and null effects
        effect_choice = np.random.choice([-1, 0, 1], p=[0.2, 0.3, 0.5])
        effect_magnitude = np.random.uniform(0.01, 0.3)
        effect_size = effect_choice * effect_magnitude

        data = generate_binary_outcome(
            n_control, n_treatment, baseline_rate, effect_size
        )
        data["domain"] = np.random.choice(domains)
        data["year"] = np.random.choice(years)
        data["test_id"] = f"BINARY_{i:05d}"
        summaries.append(data)

    # Generate continuous outcomes
    for i in range(continuous_count):
        n_control, n_treatment = generate_sample_sizes()
        baseline_mean = np.random.uniform(10, 100)
        baseline_std = np.random.uniform(5, 30)
        effect_choice = np.random.choice([-1, 0, 1], p=[0.2, 0.3, 0.5])
        effect_magnitude = np.random.uniform(0.01, 0.3)
        effect_size = effect_choice * effect_magnitude

        data = generate_continuous_outcome(
            n_control, n_treatment, baseline_mean, baseline_std, effect_size
        )
        data["domain"] = np.random.choice(domains)
        data["year"] = np.random.choice(years)
        data["test_id"] = f"CONT_{i:05d}"
        summaries.append(data)

    # Shuffle to mix types
    random.shuffle(summaries)
    return summaries

def verify_outcome_types(summaries: List[Dict[str, Any]]) -> Dict[str, int]:
    """Verify that both binary and continuous outcomes are present."""
    counts = {"binary": 0, "continuous": 0}
    for s in summaries:
        if s.get("outcome_type") == "binary":
            counts["binary"] += 1
        elif s.get("outcome_type") == "continuous":
            counts["continuous"] += 1

    logger.info(f"Outcome type verification: {counts}")
    assert counts["binary"] > 0, "No binary outcomes found!"
    assert counts["continuous"] > 0, "No continuous outcomes found!"
    assert counts["binary"] + counts["continuous"] == len(summaries), \
        "Mismatch in outcome type counts!"

    return counts

def write_summaries(summaries: List[Dict[str, Any]], filepath: Path) -> None:
    """Write summaries to CSV file."""
    if not filepath.parent.exists():
        filepath.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = summaries[0].keys()
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)

    logger.info(f"Wrote {len(summaries)} summaries to {filepath}")

def write_metadata(summaries: List[Dict[str, Any]], counts: Dict[str, int], filepath: Path) -> None:
    """Write metadata JSON file."""
    if not filepath.parent.exists():
        filepath.parent.mkdir(parents=True, exist_ok=True)

    metadata = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_records": len(summaries),
        "outcome_counts": counts,
        "parameters": {
            "total_summaries": TOTAL_SUMMARIES,
            "binary_ratio": BINARY_RATIO,
            "seed": SEED
        },
        "domains": list(set(s["domain"] for s in summaries)),
        "years": sorted(list(set(s["year"] for s in summaries)))
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Wrote metadata to {filepath}")

def main() -> None:
    """Main entry point for synthetic dataset generation."""
    logger.info("Starting synthetic dataset generation...")

    # Generate dataset
    summaries = generate_synthetic_dataset()

    # Verify outcome types
    counts = verify_outcome_types(summaries)

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Write outputs
    write_summaries(summaries, SUMMARIES_FILE)
    write_metadata(summaries, counts, METADATA_FILE)

    # Final verification
    assert SUMMARIES_FILE.exists(), "Summaries file not created!"
    assert METADATA_FILE.exists(), "Metadata file not created!"

    with open(SUMMARIES_FILE, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        row_count = sum(1 for _ in reader) - 1  # Exclude header

    assert row_count >= 10000, f"Expected >= 10000 records, got {row_count}"

    logger.info(f"SUCCESS: Generated {row_count} synthetic summaries "
                f"({counts['binary']} binary, {counts['continuous']} continuous)")

if __name__ == "__main__":
    main()
