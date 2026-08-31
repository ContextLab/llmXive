"""
Mechanism-Guided Synthetic Data Generator for Plant Stress Resilience.

This module generates synthetic metabolomic datasets with embedded ground-truth
pathways to simulate plant stress responses. The data is designed to be
compatible with the project's data models and schemas.

The generator creates:
1. Pre-stress metabolomic profiles (random baseline)
2. Stress-specific perturbations based on biological mechanisms
3. Recovery trajectories (biomass/survival) correlated with specific pathways
"""

import os
import random
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from data.models import StressType
from utils.logging import get_logger

logger = get_logger(__name__)

# Define ground-truth pathways for each stress type
# These map stress types to the specific metabolites that drive recovery
STRESS_PATHWAYS: Dict[StressType, List[str]] = {
    StressType.DROUGHT: [
        "Proline", "Glycine_Betaine", "Sucrose", "Glucose", "Fructose",
        "ABA", "Jasmonic_Acid", "Salicylic_Acid"
    ],
    StressType.HEAT: [
        "HSP70", "HSP90", "Glutathione", "Ascorbate", "Trehalose",
        "Sucrose", "Fructose", "Glucose"
    ],
    StressType.COLD: [
        "Proline", "Soluble_Sugars", "Unsaturated_Fatty_Acids",
        "Antifreeze_Proteins", "ABA", "Sucrose", "Glucose"
    ],
    StressType.SALT: [
        "Proline", "Glycine_Betaine", "Soluble_Sugars", "K+", "Na+",
        "ABA", "Jasmonic_Acid"
    ],
    StressType.NUTRIENT: [
        "Amino_Acids", "Organic_Acids", "Phytochelatins", "Flavonoids",
        "Nitrate", "Ammonium", "Phosphate"
    ]
}

# Metabolite list for baseline generation
ALL_METABOLITES = [
    "Glucose", "Fructose", "Sucrose", "Trehalose", "Starch",
    "Proline", "Glycine_Betaine", "Glutathione", "Ascorbate",
    "ABA", "Jasmonic_Acid", "Salicylic_Acid", "Ethylene",
    "HSP70", "HSP90", "Antifreeze_Proteins", "Phytochelatins",
    "Flavonoids", "Organic_Acids", "Amino_Acids",
    "K+", "Na+", "Ca2+", "Mg2+", "Nitrate", "Ammonium", "Phosphate",
    "Unsaturated_Fatty_Acids", "Soluble_Sugars"
]

def _generate_baseline_profile(n_metabolites: int) -> Dict[str, float]:
    """Generate a random baseline metabolomic profile."""
    profile = {}
    for metabolite in ALL_METABOLITES[:n_metabolites]:
        # Log-normal distribution for metabolite concentrations
        base_value = np.random.lognormal(mean=2.0, sigma=1.0)
        profile[metabolite] = round(float(base_value), 4)
    return profile

def _apply_stress_perturbation(
    profile: Dict[str, float],
    stress_type: StressType,
    intensity: float
) -> Dict[str, float]:
    """
    Apply stress-specific perturbations to the baseline profile.

    This implements the 'mechanism-guided' aspect by selectively
    increasing/decreasing metabolites associated with the specific stress.
    """
    perturbed = profile.copy()
    pathway = STRESS_PATHWAYS.get(stress_type, [])

    # Stress response: increase protective metabolites
    for metabolite in pathway:
        if metabolite in perturbed:
            # Stronger increase for pathway metabolites
            factor = 1.0 + (intensity * 0.5)
            perturbed[metabolite] = round(perturbed[metabolite] * factor, 4)

    # Some general stress response (increase ROS, etc.)
    general_stress_metabolites = ["Glutathione", "Ascorbate", "ABA"]
    for metabolite in general_stress_metabolites:
        if metabolite in perturbed:
            factor = 1.0 + (intensity * 0.3)
            perturbed[metabolite] = round(perturbed[metabolite] * factor, 4)

    return perturbed

def _generate_recovery_metric(
    profile: Dict[str, float],
    stress_type: StressType,
    time_days: int
) -> Dict[str, float]:
    """
    Generate recovery metrics based on the metabolomic profile.

    Recovery is correlated with the presence of specific pathway metabolites.
    This creates a ground-truth relationship for the model to learn.
    """
    pathway = STRESS_PATHWAYS.get(stress_type, [])

    # Calculate a 'resilience score' based on pathway metabolite levels
    pathway_sum = sum(
        profile.get(m, 0.0) for m in pathway if m in profile
    )
    total_sum = sum(profile.values())

    if total_sum == 0:
        resilience_ratio = 0.0
    else:
        resilience_ratio = pathway_sum / total_sum

    # Recovery trajectory: higher resilience ratio -> faster recovery
    # Biomass recovery (0-1 scale, 1 = full recovery)
    base_recovery = 0.3 + (resilience_ratio * 0.6)
    # Add time component: more time = more recovery (capped at 1.0)
    time_factor = min(1.0, time_days / 14.0)  # 14 days = full recovery
    biomass_recovery = min(1.0, base_recovery * (0.5 + 0.5 * time_factor))

    # Survival rate (binary-like but continuous for regression)
    # Higher resilience -> higher survival
    survival_rate = min(1.0, 0.5 + (resilience_ratio * 0.5))

    return {
        "biomass_recovery": round(float(biomass_recovery), 4),
        "survival_rate": round(float(survival_rate), 4),
        "recovery_days": time_days,
        "resilience_score": round(float(resilience_ratio), 4)
    }

def generate_synthetic_data(
    n_samples: int,
    stress_type: str,
    output_path: Optional[str] = None
) -> str:
    """
    Generate synthetic metabolomic data with ground-truth pathways.

    Args:
        n_samples: Number of samples to generate.
        stress_type: The type of stress (must match StressType enum).
        output_path: Optional path to save the Parquet file. If None,
                     generates a default path in data/raw/.

    Returns:
        The path to the generated Parquet file.

    Raises:
        ValueError: If stress_type is not a valid StressType.
        FileNotFoundError: If the output directory does not exist.
    """
    # Validate stress type
    try:
        stress = StressType(stress_type)
    except ValueError:
        raise ValueError(
            f"Invalid stress_type: '{stress_type}'. "
            f"Must be one of: {[s.value for s in StressType]}"
        )

    logger.info(f"Generating {n_samples} synthetic samples for stress: {stress.value}")

    # Prepare output directory
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"data/raw/synthetic_{stress.value}_{timestamp}.parquet"

    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Generate data
    records = []
    for i in range(n_samples):
        # Random baseline profile
        baseline = _generate_baseline_profile(n_metabolites=len(ALL_METABOLITES))

        # Random stress intensity (0.0 to 1.0)
        intensity = random.uniform(0.3, 1.0)

        # Apply stress perturbation
        stress_profile = _apply_stress_perturbation(baseline, stress, intensity)

        # Random recovery time (7 to 21 days)
        recovery_days = random.randint(7, 21)

        # Generate recovery metrics (ground truth)
        recovery = _generate_recovery_metric(stress_profile, stress, recovery_days)

        # Combine into a single record
        record = {
            "sample_id": f"{stress.value}_sample_{i:04d}",
            "stress_type": stress.value,
            "stress_intensity": round(intensity, 4),
            **stress_profile,
            **recovery,
            "recovery_index": round(
                0.6 * recovery["biomass_recovery"] + 0.4 * recovery["survival_rate"],
                4
            )
        }
        records.append(record)

    # Create DataFrame
    df = pd.DataFrame(records)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write to Parquet
    df.to_parquet(output_path, index=False)
    logger.info(f"Successfully wrote {len(df)} samples to {output_path}")

    return output_path

def generate_lodo_synthetic_datasets(
    n_datasets: int,
    stress_types: List[str],
    samples_per_dataset: int = 100,
    base_path: str = "data/raw/lodo_synthetic"
) -> List[str]:
    """
    Generate multiple distinct synthetic datasets for LODO validation.

    Each dataset will have:
    - Different noise profiles
    - Different stress vectors
    - Varying sample sizes

    Args:
        n_datasets: Number of datasets to generate.
        stress_types: List of stress types to include.
        samples_per_dataset: Target samples per dataset.
        base_path: Base directory for output files.

    Returns:
        List of paths to generated Parquet files.
    """
    os.makedirs(base_path, exist_ok=True)
    generated_files = []

    for i in range(n_datasets):
        # Select a random stress type for this dataset
        stress_type = random.choice(stress_types)
        # Vary sample size slightly
        n_samples = samples_per_dataset + random.randint(-20, 20)
        n_samples = max(50, n_samples)  # Ensure minimum sample size

        output_path = os.path.join(
            base_path,
            f"dataset_{i+1}_{stress_type}_{n_samples}.parquet"
        )

        generate_synthetic_data(
            n_samples=n_samples,
            stress_type=stress_type,
            output_path=output_path
        )
        generated_files.append(output_path)
        logger.info(f"Generated dataset {i+1}/{n_datasets}: {output_path}")

    return generated_files

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate synthetic plant stress data")
    parser.add_argument("--n-samples", type=int, default=200, help="Number of samples")
    parser.add_argument("--stress-type", type=str, default="DROUGHT",
                        help="Stress type (DROUGHT, HEAT, COLD, SALT, NUTRIENT)")
    parser.add_argument("--output", type=str, default=None, help="Output file path")

    args = parser.parse_args()

    output_file = generate_synthetic_data(
        n_samples=args.n_samples,
        stress_type=args.stress_type,
        output_path=args.output
    )
    print(f"Generated: {output_file}")
