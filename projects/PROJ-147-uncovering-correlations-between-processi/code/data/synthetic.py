"""
Physics-based synthetic data generator for rolled metals texture prediction.

This module generates synthetic datasets with known ground truth correlations
between processing conditions and texture components. It ensures:
- At least 3 distinct alloy families
- At least 50 samples per alloy family
- Known ground truth relationships for validation
- Output of ground_truth.json for verification
"""

import os
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Import from existing API surface
from code.utils.logging import get_logger, log_warning_structured
from code.config import ensure_dirs

logger = get_logger(__name__)

# Constants for physics-based generation
MIN_SAMPLES_PER_FAMILY = 50
NUM_ALLOY_FAMILIES = 3
RANDOM_SEED = 42

# Alloy family definitions with characteristic processing ranges
ALLOY_FAMILIES = {
    "aluminum_alloys": {
        "base_element": "Al",
        "typical_alloying": ["Mg", "Mn", "Si", "Cu"],
        "strain_rate_range": (0.01, 10.0),  # s^-1
        "temp_range": (200, 500),  # Celsius
        "reduction_range": (0.2, 0.8),  # fractional reduction
        "texture_factors": {
            "cube": 0.35,
            "brass": 0.25,
            "s": 0.20,
            "copper": 0.15,
            "goss": 0.05
        }
    },
    "copper_alloys": {
        "base_element": "Cu",
        "typical_alloying": ["Zn", "Sn", "Al", "Ni"],
        "strain_rate_range": (0.001, 5.0),
        "temp_range": (100, 600),
        "reduction_range": (0.1, 0.9),
        "texture_factors": {
            "cube": 0.15,
            "brass": 0.40,
            "s": 0.25,
            "copper": 0.15,
            "goss": 0.05
        }
    },
    "steel_alloys": {
        "base_element": "Fe",
        "typical_alloying": ["C", "Mn", "Cr", "Ni", "Mo"],
        "strain_rate_range": (0.001, 20.0),
        "temp_range": (400, 1100),
        "reduction_range": (0.3, 0.95),
        "texture_factors": {
            "alpha": 0.40,
            "gamma": 0.35,
            "cube": 0.10,
            "brass": 0.10,
            "other": 0.05
        }
    }
}

def _generate_physics_based_texture(
    strain_rate: float,
    temperature: float,
    reduction: float,
    alloy_family: str,
    texture_factors: Dict[str, float]
) -> Dict[str, float]:
    """
    Generate texture intensities based on physics-based relationships.

    The model incorporates:
    - Strain rate sensitivity (higher rates favor certain components)
    - Temperature effects (recrystallization vs. deformation texture)
    - Reduction ratio (accumulated strain)
    - Alloy-specific texture preferences

    Returns ODF intensities in MRD (Multiple of Random Distribution)
    """
    np.random.seed(int(strain_rate * 1000 + temperature + reduction * 1000) % (2**31))

    # Normalize inputs to [0, 1] for the model
    # Using approximate ranges from alloy families
    sr_norm = np.clip((strain_rate - 0.001) / 20.0, 0, 1)
    temp_norm = np.clip((temperature - 100) / 1000, 0, 1)
    red_norm = reduction

    # Physics-based adjustments
    # Higher strain rates tend to preserve deformation textures
    sr_factor = 1.0 + 0.3 * sr_norm

    # Higher temperatures promote recrystallization (cube texture)
    temp_factor = 1.0 + 0.5 * temp_norm

    # Higher reduction increases texture intensity
    red_factor = 1.0 + 0.4 * red_norm

    # Base texture from alloy family
    base_texture = texture_factors.copy()

    # Apply physics-based modifications
    modified_texture = {}
    total = 0.0

    for component, base_val in base_texture.items():
        # Cube texture is enhanced by temperature (recrystallization)
        if component == "cube":
            modifier = temp_factor
        # Brass and Copper textures are enhanced by strain rate
        elif component in ["brass", "copper", "s"]:
            modifier = sr_factor
        # Alpha/Gamma in steels respond to reduction
        elif component in ["alpha", "gamma"]:
            modifier = red_factor
        else:
            modifier = 1.0

        # Add noise (experimental uncertainty)
        noise = np.random.normal(0, 0.02)
        modified_texture[component] = max(0.0, base_val * modifier + noise)
        total += modified_texture[component]

    # Normalize to sum to 1.0 (probabilistic texture components)
    for component in modified_texture:
        modified_texture[component] /= total

    # Scale to MRD units (typically 1.0 = random, 2-10 = strong texture)
    mrd_scale = 2.0 + 3.0 * red_norm
    for component in modified_texture:
        modified_texture[component] *= mrd_scale

    return modified_texture

def generate_synthetic_dataset(
    num_samples_per_family: int = MIN_SAMPLES_PER_FAMILY,
    output_dir: str = "data/processed",
    seed: int = RANDOM_SEED
) -> Tuple[Dict[str, Any], Path]:
    """
    Generate a complete synthetic dataset with known ground truth.

    Args:
        num_samples_per_family: Minimum samples per alloy family (default: 50)
        output_dir: Directory to save generated data
        seed: Random seed for reproducibility

    Returns:
        Tuple of (dataset_dict, ground_truth_path)

    Raises:
        ValueError: If generation parameters are invalid
    """
    np.random.seed(seed)

    if num_samples_per_family < MIN_SAMPLES_PER_FAMILY:
        logger.warning(f"Requested {num_samples_per_family} samples, but minimum is {MIN_SAMPLES_PER_FAMILY}")
        num_samples_per_family = MIN_SAMPLES_PER_FAMILY

    # Ensure output directory exists
    ensure_dirs([output_dir])
    output_path = Path(output_dir)

    # Initialize dataset structures
    all_samples = []
    ground_truth = {
        "metadata": {
            "generator": "physics_based_synthetic_generator",
            "version": "1.0",
            "seed": seed,
            "total_samples": 0,
            "families": {}
        },
        "validation": {
            "min_samples_per_family": MIN_SAMPLES_PER_FAMILY,
            "num_families": NUM_ALLOY_FAMILIES,
            "all_families_valid": False
        }
    }

    # Generate samples for each alloy family
    for family_name, family_params in ALLOY_FAMILIES.items():
        logger.info(f"Generating {num_samples_per_family} samples for {family_name}")

        family_samples = []
        family_ground_truth = {
            "sample_count": 0,
            "processing_ranges": {
                "strain_rate": [],
                "temperature": [],
                "reduction": []
            },
            "texture_components": {k: [] for k in family_params["texture_factors"].keys()}
        }

        for i in range(num_samples_per_family):
            # Sample processing conditions from physics-based ranges
            strain_rate = np.random.uniform(*family_params["strain_rate_range"])
            temperature = np.random.uniform(*family_params["temp_range"])
            reduction = np.random.uniform(*family_params["reduction_range"])

            # Generate texture based on physics model
            texture = _generate_physics_based_texture(
                strain_rate, temperature, reduction, family_name, family_params["texture_factors"]
            )

            # Create sample record
            sample = {
                "sample_id": f"{family_name}_{i:04d}",
                "alloy_family": family_name,
                "base_element": family_params["base_element"],
                "processing": {
                    "strain_rate": round(strain_rate, 4),
                    "temperature_c": round(temperature, 2),
                    "reduction": round(reduction, 4),
                    "strain_rate_log": round(np.log10(strain_rate + 1e-6), 4)
                },
                "texture": {k: round(v, 4) for k, v in texture.items()},
                "metadata": {
                    "is_synthetic": True,
                    "generation_seed": seed + i
                }
            }

            family_samples.append(sample)
            all_samples.append(sample)

            # Track ground truth statistics
            family_ground_truth["sample_count"] += 1
            family_ground_truth["processing_ranges"]["strain_rate"].append(strain_rate)
            family_ground_truth["processing_ranges"]["temperature"].append(temperature)
            family_ground_truth["processing_ranges"]["reduction"].append(reduction)

            for comp, val in texture.items():
                family_ground_truth["texture_components"][comp].append(val)

        # Add family ground truth
        ground_truth["metadata"]["families"][family_name] = {
            "sample_count": family_ground_truth["sample_count"],
            "avg_strain_rate": round(np.mean(family_ground_truth["processing_ranges"]["strain_rate"]), 4),
            "avg_temperature": round(np.mean(family_ground_truth["processing_ranges"]["temperature"]), 2),
            "avg_reduction": round(np.mean(family_ground_truth["processing_ranges"]["reduction"]), 4),
            "dominant_texture": max(
                family_ground_truth["texture_components"].items(),
                key=lambda x: np.mean(x[1])
            )[0]
        }

        # Validate family
        if family_ground_truth["sample_count"] >= MIN_SAMPLES_PER_FAMILY:
            ground_truth["validation"]["all_families_valid"] = True
        else:
            log_warning_structured(
                "INSUFFICIENT_SAMPLES",
                f"Family {family_name} has {family_ground_truth['sample_count']} samples < {MIN_SAMPLES_PER_FAMILY}"
            )

    # Update total count
    ground_truth["metadata"]["total_samples"] = len(all_samples)

    # Convert lists to stats for ground truth file
    for family_name in ground_truth["metadata"]["families"]:
        gt_family = ground_truth["metadata"]["families"][family_name]
        # We already computed averages, no need to store full lists in JSON

    # Save synthetic dataset
    dataset_path = output_path / "synthetic_dataset.json"
    with open(dataset_path, 'w') as f:
        json.dump({"samples": all_samples}, f, indent=2)

    # Save ground truth
    ground_truth_path = output_path / "ground_truth.json"
    with open(ground_truth_path, 'w') as f:
        json.dump(ground_truth, f, indent=2)

    logger.info(f"Generated {len(all_samples)} synthetic samples across {NUM_ALLOY_FAMILIES} families")
    logger.info(f"Dataset saved to {dataset_path}")
    logger.info(f"Ground truth saved to {ground_truth_path}")

    return {"samples": all_samples}, ground_truth_path

def validate_ground_truth(ground_truth_path: Path) -> bool:
    """
    Validate that the generated ground truth meets requirements.

    Checks:
    - At least 3 distinct alloy families
    - At least 50 samples per family
    - Ground truth file exists and is valid JSON

    Args:
        ground_truth_path: Path to ground_truth.json

    Returns:
        True if validation passes, False otherwise
    """
    try:
        with open(ground_truth_path, 'r') as f:
            ground_truth = json.load(f)

        # Check number of families
        families = ground_truth.get("metadata", {}).get("families", {})
        if len(families) < NUM_ALLOY_FAMILIES:
            logger.error(f"Expected {NUM_ALLOY_FAMILIES} families, found {len(families)}")
            return False

        # Check samples per family
        for family_name, family_data in families.items():
            count = family_data.get("sample_count", 0)
            if count < MIN_SAMPLES_PER_FAMILY:
                logger.error(f"Family {family_name} has only {count} samples < {MIN_SAMPLES_PER_FAMILY}")
                return False

        # Check validation flag
        if not ground_truth.get("validation", {}).get("all_families_valid", False):
            logger.error("Ground truth validation flag is False")
            return False

        logger.info("Ground truth validation passed")
        return True

    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to validate ground truth: {e}")
        return False

if __name__ == "__main__":
    # Run generator when executed directly
    logger.info("Starting synthetic data generation...")
    dataset, gt_path = generate_synthetic_dataset(
        num_samples_per_family=MIN_SAMPLES_PER_FAMILY,
        output_dir="data/processed"
    )

    # Validate
    if validate_ground_truth(gt_path):
        logger.info("Synthetic data generation completed successfully")
    else:
        logger.error("Synthetic data generation failed validation")
        exit(1)
